import logging
import math
import re
import shutil
import string
import sys
import time
import timbermafia.formats
from timbermafia.rainbow import RainbowStreamHandler, RainbowFileHandler, palette_dict
from timbermafia.formatters import TimbermafiaFormatter
import timbermafia.utils as utils


log = logging.getLogger(__name__)

FIXED_LENGTH_FIELDS = ['asctime', 'levelname']

STYLES = {
    'minimalist': {
        'default_format': '{asctime} _ {message}',
    }
}

STYLE_DEFAULTS = {
    'smart_names': True,
    'justify': {
        'default': str.rjust,
        'left': ['message'],
        # 'right': ['funcName'],
        },
    'time_format': '%H:%M:%S',
    'padding': {
        'default': 0.2,
        'message': 0.8,
        # 'name': 0.15,
        # 'funcName': 0.15,
    },
    'truncate': ['name', 'message'],
    'truncation_chars': '...',
    'log_format': 'test: _| {asctime:u} _| {name} {levelname}'
                  ' _| {name}.{funcName} __>> {message:b,>118} END',
    'column_escape': '_',
    'format_style': '{',
    'fit_to_terminal': False,
    'n_columns': 100,
}


class Column:

    def __init__(self, fmt, justify=str.rjust, time_fmt='%H:%M:%S'):
        # self.fmt = fmt
        fmt = fmt.lstrip().rstrip()
        self.time_fmt = time_fmt
        self.fmt = fmt
        self.fmt_basic = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        self.fields = re.findall(r'(?<=\{)[a-zA-Z]+(?=[\}:])', fmt)
        self.justify = justify
        self.multiline = False
        self.adaptive_fields = [x for x in self.fields
                                if x not in FIXED_LENGTH_FIELDS]

        # Count any space used by the template string that
        # won't be formatted with a log record component
        self.reserved_padding = 0
        self.count_reserved_padding()

    def count_reserved_padding(self):
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
        # print(self.fields)
        # If time is present add it.
        if 'asctime' in self.fields:
            self.reserved_padding += self.time_format_length

        # If levelname present add it.
        if 'levelname' in self.fields:
            self.reserved_padding += self.max_levelname_length

    @property
    def max_levelname_length(self):
        """Gets the character length of the maximum level name."""
        return len(max(logging._nameToLevel.keys(), key=len))

    @property
    def time_format_length(self):
        """Returns the length in chars of the asctime
        with the current time format"""
        return len(time.strftime(self.time_fmt))

    def __str__(self):
        return 'Column("{}")'.format(self.fmt)

    def truncate_input(self, record_dict):
        """Truncate the elements in place as needed.
        Need to account for non-formatted space too!"""
        fmt = self.fmt_basic
        # print(fmt)
        new_fmt = ''
        while fmt and len(new_fmt) <= self.reserved_padding:
            c = fmt[-1]
            # print(c)
            # If not a format component
            if c != '}':
                new_fmt = new_fmt + c
                fmt = fmt[:-1]
            else:
                index = fmt.rfind('{')
                print(index)
                print(fmt[index:])
                print(fmt)
                record_component = fmt[index:][1:-1]
                print('record component:', record_component)
                s = record_dict[record_component]
                fmt = fmt[:index]
                if len(s) > (self.reserved_padding - len(new_fmt)):
                    print('cannot fit all this component in')

            # At this point get the new format and the altered record components.


class Separator:
    def __init__(self, content, column_escape):
        self.content = content
        self.column_escape = column_escape
        self.content_escaped = content.replace(column_escape, '')
        self.length = len(self.content_escaped)
        self.multiline = '__' in self.content
        # print(self.__dict__)

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

        # Explicitly set the properties a logging.Formatter object
        # expects that need custom verification
        self.format_style = kwargs.get('format_style', conf['format_style'])

        self.log_format = kwargs.get('log_format', conf['log_format'])
        self.time_format = kwargs.get('time_format', conf['time_format'])
        print(self.log_format)
        # Bundle other settings in a dict.
        self.conf = conf

    @property
    def format_style(self):
        return self._fmt_style

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

    # @property
    # def time_format_length(self):
    #     """Returns the length in chars of the asctime
    #     with the current time format"""
    #     return len(time.strftime(self.time_format))

    @property
    def max_levelname_length(self):
        """Gets the character length of the maximum level name."""
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
    def n_columns(self):
        if self.conf['fit_to_terminal']:
            return shutil.get_terminal_size().columns
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
    def single_line_output(self):
        """Property to determine if the output with this format
        is restricted to a single line output"""
        if not self._column_dict:
            self.generate_column_settings()
        if self._single_line_output is None:
            # print([c.multiline for c in self._column_dict.values()])
            b = all([c.multiline is False for c in self._column_dict.values()])
            # print('bool says:', b)
            self._single_line_output = b
        return self._single_line_output

    def calculate_padding(self, column_dict, separator_dict, template):
        """Function to evaluate column padding widths"""

        # Get the total reserved space from each column,
        # which does not account for any adaptive
        # length record components.
        total_used_space = sum([c.reserved_padding for c
                                in column_dict.values()])

        # Add spaces from the template
        # ws = [i for i in template if i.is]
        non_special_chars = ''.join(
            [s for s in re.findall(r'(.*?)\{.*?\}', template) if s]
        )
        # print(non_special_chars)
        print(len(non_special_chars))
        total_used_space += len(non_special_chars)

        # Add space used on separators
        separator_padding = 0
        for s in separator_dict.values():
            separator_padding += s.length
        total_used_space += separator_padding
        print(total_used_space)

        adaptive_fields = [
            x for y in list(c.adaptive_fields for c
                            in column_dict.values())
            for x in y
        ]
        # print(adaptive_fields)

        # Normalise adaptive fields to space left
        space_for_adaptive = self.n_columns - total_used_space
        print('space remaining', space_for_adaptive)

        adaptive_fields_dict = {}
        weights = self.conf['padding']

        for i, f in enumerate(adaptive_fields):
            weight = weights.get(f, weights['default'])
            adaptive_fields_dict[i] = {'field': f, 'weight': weight}

        # print(adaptive_fields_dict)

        total_weights = sum(v['weight'] for v in adaptive_fields_dict.values())
        # print(total_weights)
        for d in adaptive_fields_dict.values():
            d['char_length'] = math.floor(
                (d['weight'] / total_weights) * space_for_adaptive
            )
        # print(adaptive_fields_dict)

        ad2 = {}
        for d in adaptive_fields_dict.values():
            f = d['field']
            if f not in ad2:
                ad2[f] = d['char_length']

        # print(ad2)

        # We've used floors so might have multiple chars to spare.
        # Consider incrementing the message char_length here if the sum
        # is below the space_for_adaptive

        test_padding = 0
        for c in column_dict.values():
            for f in c.adaptive_fields:
                char_length = ad2[f]
                c.reserved_padding += char_length
            test_padding += c.reserved_padding

        # print(test_padding, separator_padding)
        deficit = self.n_columns - test_padding - separator_padding

    def evaluate_multiline_possibility(self, column_dict):
        """Figure out it is possible that a column requires
        multiple lines of output"""
        for c in column_dict.values():
            truncate = False
            if c.adaptive_fields:
                for field in c.adaptive_fields:
                    if field in self.conf['truncate']:
                        truncate = True
            if c.adaptive_fields and not truncate:
                c.multiline = True

    def set_column_justifications(self, column_dict):
        """If required changes the Column.justify values
        to non-defaults."""
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

                # print(bool(justification_settings))
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

        print(parts)
        print(self.time_format)
        column_dict = {k: Column(
            part, justify=self.default_justify,
            time_fmt=self.time_format
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

        print(column_dict)
        print(separator_dict)
        print(template)
        self.set_column_justifications(column_dict)
        self.calculate_padding(column_dict, separator_dict, template)
        self.evaluate_multiline_possibility(column_dict)

        # Internally assign these attributes.
        self._column_dict = column_dict

        return {
            'columns': column_dict,
            'separators': separator_dict,
            'template': template
        }


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
        style=None, fmt=None, stream=sys.stdout, filename=None,
        clear=False, basic_files=True, handlers=None, level=logging.DEBUG,
        ):
    """Function for basic configuration of timbermafia logging.

    Describe Args here
    """
    logging._acquireLock()  # don't like that this is protected

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
        my_style = Style(style=style, fmt=fmt)

        if use_custom_formatter:
            custom_formatter = configure_custom_formatter(my_style)

        use_default_formatter = filename and not basic_files
        if use_default_formatter:
            # In line below we'll add the basic format from the style property
            default_formatter = configure_default_formatter(my_style)

        # Add stream handler if specified
        if stream:
            # h = logging.StreamHandler(stream=sys.stdout)
            h = RainbowStreamHandler(stream=sys.stdout)
            h.setFormatter(custom_formatter)
            handlers.append(h)

        # Add file handler if specified
        if filename:
            h = logging.FileHandler(filename)
            if basic_files:
                h.setFormatter(default_formatter)
            else:
                h.setFormatter(custom_formatter)

        for h in handlers:
            h.setLevel(level)
            logger.addHandler(h)

        logger.setLevel(level)

        print('- timbermafia has configured handlers:')
        for h in handlers:
            print('  -', h)

    finally:
        logging._releaseLock()  # again don't like this


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
