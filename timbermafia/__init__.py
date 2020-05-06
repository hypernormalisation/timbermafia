import logging
import math
import re
import shutil
import string
import sys
import textwrap
import time
import timbermafia.formats
from timbermafia.palettes import PALETTE_DICT
from timbermafia.formatters import TimbermafiaFormatter
import timbermafia.utils as utils


log = logging.getLogger(__name__)

FIXED_LENGTH_FIELDS = ['asctime', 'levelname']

STYLES = {
    'minimalist': {
        'format': '{asctime} _ {message}',
    }
}

STYLE_DEFAULTS = {
    'smart_names': True,
    'justify': {
        'default': str.rjust,
        'left': ['message'],
        },
    'time_format': '%H:%M:%S',
    'padding': {
        'default': 0.2,
        'message': 1.4,
        'funcName': 0.3,
        # 'module': 0.14,
    },
    'truncate': ['name', 'funcName'],
    'truncation_chars': '\u2026',
    'format': '{asctime:u} _| {levelname} _| {name}.{funcName} __>> {message:>15} ',
    'column_escape': '_',
    'format_style': '{',
    'fit_to_terminal': True,
    'n_columns': 120,
    'max_width': 180,
    'clean_output': True,
    'monochrome': False,
    'short_levels': True,
}


class Column:

    def __init__(
            self, fmt, justify=str.rjust,
            time_fmt='%H:%M:%S',
            truncation_fields=None,
            truncation_chars='...',
            short_levels=None
            ):
        fmt = fmt.lstrip().rstrip()
        self.time_fmt = time_fmt
        self.fmt = fmt
        self.truncation_chars = truncation_chars
        self.fmt_basic = re.sub(r'(?<=\w):\S+?(?=[\}:])', '', fmt)
        self.fields = re.findall(r'(?<=\{)[a-zA-Z]+(?=[\}:])', fmt)

        self.truncate_enabled = False
        if truncation_fields:
            for f in self.fields:
                if f in truncation_fields:
                    self.truncate_enabled = True

        self.justify = justify
        # self.multiline = False
        self.short_levels = short_levels

        self.adaptive_fields = [x for x in self.fields
                                if x not in FIXED_LENGTH_FIELDS]

        # Count any space used by the template string that
        # won't be formatted with a log record component
        self.reserved_padding = 0
        self.count_static_padding_amount()

        # Placeholder for the textwrap.TextWrapper instance
        # that will be used in case of multiline breaks.
        self._wrapper = None

    def return_simplified_fmt(self, fmt):
        return re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)

    def return_field_from_format(self, fmt):
        s = self.return_simplified_fmt(fmt)
        return s[1:-1]

    @property
    def wrapper(self):
        if not self._wrapper:
            self._wrapper = textwrap.TextWrapper(
                width=self.reserved_padding,
                break_long_words=False,
            )
        return self._wrapper

    @property
    def fixed_length(self):
        if not self.adaptive_fields:
            return True
        return False

    @property
    def truncation_chars_length(self):
        return len(self.truncation_chars)

    def count_static_padding_amount(self):
        """
        Count the padding as much as is possible without
        considering adaptive fields. If no adaptive fields are present
        the count is complete.

        Considers space in the format string that will not be formatted
        by a log record component, and the fixed length asctime and max
        length of any log levelname.
        """
        # Add space from the template that won't be formatted
        contents_no_formats = re.sub(r'\{\S+?\}', '', self.fmt)
        self.reserved_padding += len(contents_no_formats)
        # If time is present add it.
        if 'asctime' in self.fields:
            self.reserved_padding += self.time_format_length
        # If levelname present add it.
        if 'levelname' in self.fields:
            self.reserved_padding += self.max_levelname_length

    @property
    def max_levelname_length(self):
        """Gets the character length of the maximum level name."""
        if self.short_levels:
            return 1
        return len(max(logging._nameToLevel.keys(), key=len))

    @property
    def time_format_length(self):
        """Returns the length in chars of the asctime
        with the current time format"""
        return len(time.strftime(self.time_fmt))

    @property
    def empty_padding_string(self):
        return ' ' * self.reserved_padding

    def __str__(self):
        return 'Column("{}")'.format(self.fmt)

    def format_multiline(self, record_dict):
        """
        Function to take a LogRecord's dict with the relevant
        fields, and split the message over multiple lines.

        Returns a list of formatted lines.
        """
        # Figure out the structure of the multiline output by
        # first using a textwrap with the basic version
        # of the format
        basic_string = self.fmt_basic.format(**record_dict)
        basic_lines = self.wrapper.wrap(basic_string)

        line_length_map = {index: len(line) for index, line
                           in enumerate(basic_lines)}

        # This will be processed from the beginning until gone.
        fmt_to_parse = self.fmt

        # Containers to be reset each line.
        line_content = ''
        line_fmt = ''
        formatted_lines = []
        line_record_dict = {}
        current_line_index = 0
        this_line_max_length = line_length_map[current_line_index]

        # Iterate over the format and create a new format and specialised
        # format_dict contents for this line.
        while fmt_to_parse:

            # Get the first character in the format string
            c = fmt_to_parse[0]
            # If it's not a format, simply add to this_fmt and remove
            # from fmt_to_be_parsed
            if c != '{':

                # Remove leading whitespace characters in new lines.
                if c.isspace() and len(line_content) == 0:
                    fmt_to_parse = fmt_to_parse[1:]
                    continue

                line_fmt += c
                line_content += c
                fmt_to_parse = fmt_to_parse[1:]
            
            # Otherwise we have found a format.
            # Match it but don't pull it out yet.
            else:
                ptn = r'^(?P<first_format>{\S+?}).*'
                first_format = re.match(
                    ptn, fmt_to_parse
                ).group('first_format')
                line_fmt += first_format

                # Get content
                this_field = self.return_field_from_format(first_format)
                this_content = record_dict[this_field]

                # Remove leading whitespace characters on new lines.
                if this_content[0].isspace() and len(line_content) == 0:
                    this_content = this_content[1:]
                    record_dict[this_field] = record_dict[this_field][1:]

                # If the whole thing takes us over the limit, slice off what
                # we can fit, AND DO NOT PURGE THE FORMAT FROM THE fmt_to_parse
                if (len(line_content) +
                        len(this_content)) > this_line_max_length:
                    space_this_line = this_line_max_length - len(line_content)

                    content_to_add = this_content[:space_this_line]

                    # Remove this from the total record dict and add it to the
                    # total content for this line.
                    line_content += content_to_add
                    record_dict[this_field] = record_dict[this_field][space_this_line:]
                    line_record_dict[this_field] = utils.TMString(content_to_add)

                # Else we can add the thing wholesale
                # Also remove the format space from the fmt_to_parse
                else:
                    line_content += this_content
                    line_record_dict[this_field] = utils.TMString(this_content)
                    fmt_to_parse = re.sub(first_format, '', fmt_to_parse)

            # If we've hit the limit, push these lines and
            # empty the containers
            if len(line_content) == this_line_max_length:

                # If there is a deficit between the total reserved padding
                # and the max length from the textwrap, make it up here
                # with additional padding.
                to_pad = self.reserved_padding - this_line_max_length
                if to_pad:
                    line_fmt += (' ' * to_pad)
                s = line_fmt.format(**line_record_dict)
                formatted_lines.append(s)

                # If still fmt_to_parse, reset containers and increment
                # line index to get the new max length of the line.
                if fmt_to_parse:
                    current_line_index += 1
                    this_line_max_length = line_length_map[current_line_index]
                    line_content = ''
                    line_fmt = ''
                    line_record_dict = {}

            # If we've run out of fmt to parse, we need to then add
            # some padding to finish out this row of the column.
            elif not fmt_to_parse:
                extra_room = self.reserved_padding - len(line_content) + len(line_fmt)
                line_fmt = self.justify(line_fmt, extra_room)
                s = line_fmt.format(**line_record_dict)
                formatted_lines.append(s)

        return formatted_lines

    def justify_and_pad_input(self, record_dict):
        """Func to take output needing padding and justification
        and perform it."""
        # Need the basic formatted content to know how much to
        # pad the format
        fmt = self.fmt
        basic_content = self.fmt_basic.format(**record_dict)
        extra_room = self.reserved_padding - len(basic_content) + len(fmt)
        # Use the specified justify function to pad the format string.
        fmt = self.justify(fmt, extra_room)
        return fmt.format(**record_dict)

    def truncate_input(self, record_dict):
        """Truncate the format and content using the allotted space."""
        fmt_to_parse = self.fmt
        new_fmt = ''

        # Contains the output content as it is pushed back
        running_total_content = ''
        fitted_component_dict = {}

        # The allowed padding is the reserved padding minus the
        # length of the truncation chars
        allowed_padding = self.reserved_padding - self.truncation_chars_length
        while fmt_to_parse and len(new_fmt) <= allowed_padding:

            # Final char in fmt string
            c = fmt_to_parse[-1]

            # If not a format component, trim the character from the
            # old format and push it to the new one, then continue.
            if c != '}':
                new_fmt = c + new_fmt
                running_total_content = c + running_total_content
                fmt_to_parse = fmt_to_parse[:-1]
                continue

            # Otherwise we have found a {format}
            # Remove the format from the to_parse fmt
            # and push it into the new_fmt
            ptn = r'.*(?P<last_format>{\S+})$'
            last_format = re.match(ptn, fmt_to_parse).group('last_format')
            new_fmt = last_format + new_fmt
            fmt_to_parse = re.sub(last_format, '', fmt_to_parse)

            # Now figure out the field and get the corresponding contents
            this_field = self.return_field_from_format(last_format)
            this_content = record_dict[this_field]

            # If the whole thing fits, add the contents in full.
            # Add an entry in the new component dict, then continue
            if (len(this_content) +
                    len(running_total_content)) < allowed_padding:
                running_total_content = this_content + running_total_content
                fitted_component_dict[this_field] = this_content
                continue

            # If it does not, curtail the content, push the trunc chars
            # to the content, and break the while loop
            space = allowed_padding - len(running_total_content)

            # Take the last n=space chars from the end of the contents
            partial_content = this_content[-space:]
            # Add the truncation characters to the start of the string.
            partial_content = self.truncation_chars + partial_content
            fitted_component_dict[this_field] = partial_content
            break

        # Turn all contents into TMStrings so they can pick
        # up the fmt_spec
        final_dict = {}
        for field, s in fitted_component_dict.items():
            final_dict[field] = utils.TMString(s)

        # Finally, format the full string and return.
        return new_fmt.format(**final_dict)


class Separator:
    def __init__(self, content, column_escape):
        self.content = content
        self.column_escape = column_escape
        self.content_escaped = content.replace(column_escape, '')
        self.length = len(self.content_escaped)
        self.multiline = '__' in self.content

    def return_separator_string(self, line_index):
        """Return a string for the separator
        based on an input line number index (starting from zero).
        multiline always return the normal, otherwise
        for line_numbers above 0 we give empty space
        the length of the separator.
        """
        if self.multiline or line_index == 0:
            return self.content_escaped
        return ' ' * self.length


class Style:
    """
    Class to hold style settings used in timbermafia
    logging subclasses.
    """
    def __init__(self, preset=None, **kwargs):

        # Establish which settings to use
        conf = STYLE_DEFAULTS
        if preset:
            try:
                conf.update(STYLES[preset])
            except KeyError as e:
                print(e)
                raise

        # Protected settings
        self._fmt = None
        self._time_fmt = None
        self._fmt_style = None
        self._column_dict = {}
        self._single_line_output = None
        self._fields = None

        # Get the requested colour palette for the log levels.
        palette_key = kwargs.get('palette', 'sensible')
        self.palette_key = palette_key
        self.palette = PALETTE_DICT[palette_key]

        # Explicitly set the properties a logging.Formatter object
        # expects that need custom verification.
        self.format_style = kwargs.get('format_style', conf['format_style'])
        log_format = kwargs.get('format')
        if not log_format:
            log_format = conf['format']
        self.log_format = log_format
        self.time_format = kwargs.get('time_format', conf['time_format'])

        # Bundle other settings in a dict.
        self.conf = conf

        # Placeholder for generated settings
        self.generated_settings = None

    @property
    def format_style(self):
        return self._fmt_style

    @property
    def monochrome(self):
        return self.conf['monochrome']

    @format_style.setter
    def format_style(self, s):
        valid_formats = ['{']
        if s not in valid_formats:
            raise ValueError(f'Format style {s} not accepted,'
                             f' valid are{",".join(valid_formats)}')
        self._fmt_style = s

    @property
    def format(self):
        return self._fmt

    @format.setter
    def format(self, f):
        # Put a regex here to ensure the format is valid.
        self._fmt = f

    @property
    def time_format(self):
        return self._time_fmt

    @time_format.setter
    def time_format(self, f):
        # regex check here
        self._time_fmt = f

    @property
    def max_levelname_length(self):
        """Gets the character length of the maximum level name."""
        if self.short_levels:
            return 1
        return len(max(logging._nameToLevel.keys(), key=len))

    @property
    def column_escape(self):
        return self.conf['column_escape']

    @property
    def simple_log_format(self):
        """Return the format without any unnecessary whitespace or fmt_spec"""
        fmt = self.log_format
        fmt = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        fmt = re.sub(self.column_escape, '', fmt)
        return fmt

    @property
    def no_ansi_log_format(self):
        fmt = self.log_format
        fmt = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        return fmt

    @property
    def fit_to_terminal(self):
        if self.conf['fit_to_terminal']:
            return True
        return False

    @property
    def max_width(self):
        return self.conf.get('max_width', False)

    @property
    def short_levels(self):
        return self.conf.get('short_levels', False)

    @property
    def n_columns(self):
        if self.fit_to_terminal:
            n = shutil.get_terminal_size().columns
            if self.max_width:
                if n > self.max_width:
                    return self.max_width
            return n
        else:
            return self.conf.get('n_columns')

    @property
    def default_justify(self):
        return self.conf['justify'].get('default', str.rjust)

    @property
    def fields(self):
        if not self._column_dict:
            self.generate_column_settings()
        if self._fields is None:
            self._fields = [
                x for y in list(c.fields for c
                                in self._column_dict.values())
                for x in y
            ]
        return self._fields

    @property
    def clean_output(self):
        """
        If true, removes the following:
        - "root." from logger names
        """
        return self.conf['clean_output']

    @property
    def single_line_output(self):
        """Property to determine if the output with this format
        is restricted to a single line output"""
        if not self._column_dict:
            self.generate_column_settings()
        if self._single_line_output is None:
            b = all([c.multiline is False for c in self._column_dict.values()])
            self._single_line_output = b
        return self._single_line_output

    def calculate_padding(self, column_dict, separator_dict, template):
        """
        Function to evaluate column padding widths.
        """
        # Get the total reserved space from each column,
        # which does not account for any adaptive
        # length record components.
        total_used_space = sum([c.reserved_padding for c
                                in column_dict.values()])

        # Add spaces from the template
        non_special_chars = ''.join(
            [s for s in re.findall(r'(.*?)\{.*?\}', template) if s]
        )
        nsp_len = len(non_special_chars)
        total_used_space += len(non_special_chars)

        # Add space used on separators
        separator_padding = 0
        for s in separator_dict.values():
            separator_padding += s.length
        total_used_space += separator_padding

        adaptive_fields = [
            x for y in list(c.adaptive_fields for c
                            in column_dict.values())
            for x in y
        ]

        # Normalise adaptive fields to space left
        space_for_adaptive = self.n_columns - total_used_space
        if space_for_adaptive < 5:
            raise ValueError('Column width insufficient for this configuration.'
                             ' Specify a higher column width.')
        adaptive_fields_dict = {}
        weights = self.conf['padding']

        for i, f in enumerate(adaptive_fields):
            weight = weights.get(f, weights['default'])
            adaptive_fields_dict[i] = {'field': f, 'weight': weight}

        total_weights = sum(v['weight'] for v in adaptive_fields_dict.values())
        for d in adaptive_fields_dict.values():
            d['char_length'] = math.floor(
                (d['weight'] / total_weights) * space_for_adaptive
            )

        ad2 = {}
        for d in adaptive_fields_dict.values():
            f = d['field']
            if f not in ad2:
                ad2[f] = d['char_length']

        # We've used floors so might have multiple chars to spare.
        # Consider incrementing the message char_length here if the sum
        # is below the space_for_adaptive
        all_column_padding = 0
        for c in column_dict.values():
            for f in c.adaptive_fields:
                char_length = ad2[f]
                c.reserved_padding += char_length
            all_column_padding += c.reserved_padding

        # Iter over the columns and if we have adaptive fields, increment the
        # reserved padding to take us to the max.
        deficit = self.n_columns - all_column_padding - separator_padding - nsp_len
        while deficit > 0:
            for c in column_dict.values():
                if c.adaptive_fields:
                    c.reserved_padding += 1
                    deficit -= 1
                    if deficit == 0:
                        break

    def set_column_justifications(self, column_dict):
        """
        If required changes the Column.justify values
        to non-defaults.
        """
        just_conf = self.conf['justify']
        to_ljust = just_conf.get('left', [])
        to_rjust = just_conf.get('right', [])
        to_cjust = just_conf.get('center', [])
        just_d = {
            str.ljust: to_ljust,
            str.rjust: to_rjust,
            str.center: to_cjust,
        }

        for c in column_dict.values():
            justification_settings = []
            for func, fields_to_just in just_d.items():
                for f in c.fields:
                    if f in fields_to_just:
                        if not justification_settings:
                            c.justify = func
                            justification_settings.append(f)
                        else:
                            justification_settings.append(f)
                            print('Warning: multiple contagious justifications '
                                  f'specified in {c}'
                                  f' for fields: {",".join(justification_settings)}. '
                                  f'Using {c.justify}')

    def generate_column_settings(self):
        """
        Function to parse the log format to understand any column
        and separator specification, and return the information
        in a dict.
        """
        # Reset recorded settings from any possible previous configs.
        self._single_line_output = None
        self._fields = None

        fmt = self.log_format
        partial_text = re.sub(utils.column_sep_pattern,
                              self.column_escape, fmt)
        parts = partial_text.split(self.column_escape)

        # Filter parts without a log record component
        parts = [ x for x in parts if
            utils.logrecord_present_pattern.match(x)
        ]

        column_dict = {k: Column(
            part, justify=self.default_justify,
            time_fmt=self.time_format,
            truncation_fields=self.conf['truncate'],
            truncation_chars=self.conf['truncation_chars'],
            short_levels=self.short_levels
            ) for k, part in zip(string.ascii_uppercase, parts)
        }

        # Create a template for the formatted separator and column
        # content to go into.
        template = fmt
        for key, c in column_dict.items():
            template = template.replace(c.fmt, '{'+key+'}', 1)

        separators = re.findall(utils.column_sep_pattern, fmt)
        separator_dict = {
            k: Separator(sep, self.column_escape) for k, sep in
            zip(string.ascii_lowercase, separators)
        }

        # Now substitute the separators sequentially in case of
        # identical separators.
        for key, s in separator_dict.items():
            template = template.replace(s.content, '{'+key+'}', 1)

        self.set_column_justifications(column_dict)
        self.calculate_padding(column_dict, separator_dict, template)

        # Internally assign these attributes.
        self._column_dict = column_dict

        d = {
            'columns': column_dict,
            'separators': separator_dict,
            'template': template
        }
        self.generated_settings = d
        return d


def configure_custom_formatter(style):
    """Simple function to use a Style to create
    a timbermafia formatter instance."""
    return TimbermafiaFormatter(
        style.log_format,
        style.time_format,
        style.format_style,
        timbermafia_style=style
    )


def configure_default_formatter(style):
    """Simple function to use a Style to create
    a basic logging.Formatter instance."""
    return logging.Formatter(
        style.simple_log_format,
        style.time_format,
        style.format_style
    )


def basic_config(
        style=None, format=None, stream=sys.stdout, filename=None,
        palette='sensible', silent=False,
        clear=False, basic_files=True, handlers=None, level=logging.DEBUG,
        ):
    """Function for basic configuration of timbermafia logging.

    Describe Args here
    """
    logging._acquireLock()
    try:
        # Reference to the root logger
        logger = logging.root

        # Reset existing handlers if needed
        handlers = handlers if handlers else []
        if clear:
            for h in logger.handlers[:]:
                logger.removeHandler(h)
                h.close()

        # Only create formatters and styles as required.
        use_custom_formatter = stream or (filename and not basic_files)
        custom_formatter, default_formatter = None, None

        # If the given style is a Style instance, use it.
        # Else generate a style from the preset.
        my_style = style
        if not isinstance(style, Style):
            if format:
                my_style = Style(preset=style, format=format, palette=palette)
            else:
                my_style = Style(preset=style, palette=palette)

        if use_custom_formatter:
            custom_formatter = configure_custom_formatter(my_style)

        use_default_formatter = filename and not basic_files
        if use_default_formatter:
            # In line below we'll add the basic format from the style property
            default_formatter = configure_default_formatter(my_style)

        # Add stream handler if specified
        if stream:
            h = logging.StreamHandler(stream=sys.stdout)
            # h = RainbowStreamHandler(stream=sys.stdout, palette=palette)
            h.setFormatter(custom_formatter)
            handlers.append(h)

        # Add file handler if specified
        if filename:
            h = logging.FileHandler(filename)
            if basic_files:
                h.setFormatter(default_formatter)
            else:
                h.setFormatter(custom_formatter)

        # Set logging levels.
        for h in handlers:
            h.setLevel(level)
            logger.addHandler(h)
        logger.setLevel(level)

        if not silent:
            print('- timbermafia has configured handlers:')
            for h in handlers:
                print('  -', h)

    finally:
        logging._releaseLock()


def resize_test():
    import timbermafia as tm
    tm.basic_config()
    import logging
    return logging.getLogger(__name__)

class Logged:
    """
    Inherit from this class to provide a mixin logger via
    the log property.

    The log name ensures the root logger is in the logger
    hierarchy, and that its handlers can be used.
    """
    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'root.{self.__class__.__name__}')
