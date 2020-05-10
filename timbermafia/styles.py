"""Styles for timbermafia.

Herein the Style class is defined, which relies upon the Column
and Separator classes to function.

Users can generate their own styles and use them in timbermafia
or in python logging more generally.
"""

import collections.abc
import copy
import logging
import math
import re
import shutil
import string
import textwrap
import time
import timbermafia.utils as utils

# LogRecord fields for which we can derive a fixed
# or a maximum length.
_fixed_length_fields = ['asctime', 'levelname']

# Used to specify justifications by a letter or name.
_just_functions_map = {
    'l': str.ljust,
    'left': str.ljust,
    'r': str.rjust,
    'right': str.rjust,
    'c': str.center,
    'center': str.center,
}

# To print the Style status to the user, map
# the justification function to a string.
_just_label_map = {
    str.ljust: 'left',
    str.rjust: 'right',
    str.center: 'center'
}

# These are the default style that all styles will pick up
# and optionally override.
_style_defaults = {

    # Format options
    'format': '{asctime:u} _| {levelname} '
              '_| {name}.{funcName} __>> {message:>231}',
    'datefmt': '%H:%M:%S',

    # Justification options
    'justify': {
        'default': str.rjust,
        'message': str.ljust,
    },

    # Padding options - these are weights for assigning
    # space for adaptive-length LogRecord components
    # depending on the width.
    'padding_weights': {
        'default': 1.0,
        'message': 6.0,
        # 'funcName': 1,
    },

    # Truncation options
    'truncate_fields': ['funcName'],
    'truncation_chars': '\u2026',

    # Terminal width options
    'fit_to_terminal': False,
    'width': 100,
    'max_width': 160,

    # Character indicating column escapes
    'column_escape': '_',

    # Boolean options
    'clean_output': True,  # Cleans certain redundant info in LogRecords
    'colourised_levels': True,  # Colourise levels based on LogRecord level
    'short_levels': False,  # Abbreviate level names from e.g. INFO to I
}

# A map of preset style names to their configurations.
# These are applied on top of the STYLE_DEFAULTS
_default = {'description': 'Default style for timbermafia.'}

_minimalist = {
    'description': 'Display only the time and message, good for '
                   'verbose log messages.',
    'format': '{asctime} _| {message}',
    'width': 80,
}

_compact = {
    'description': 'Give lots of log record information in a small space.',
    'format': '{asctime} _ {levelname} _ {name}.{funcName} _ {message:>231}',
    'short_levels': True,
    'width': 100,
}

_boxy = {
    'description': 'A detailed, boxy looking output fit to the terminal.',
    'format': '__| {asctime:u} __| {levelname:u} __| {name} __| '
              '{funcName} __| {message:>231} __|',
    'truncate_fields': [],
    'fit_to_terminal': True,
    'padding_weights': {
        'default': 1.0,
        'message': 5.0,
        'funcName': 1.5
    },
    'max_width': False,
    'short_levels': True
}

_plain = {
    'description': 'A style emulating vanilla logging.',
    'format': '{asctime} {name} > {message}',
    'width': 100,
    'max_width': 200,
    'fit_to_terminal': True,
    'justify': {'default': str.ljust},
    'colourised_levels': False,
    'truncate_fields': [],
}

style_map = {
    'default': _default,
    'minimalist': _minimalist,
    'compact': _compact,
    'boxy': _boxy,
    'plain': _plain,
}


class Column:
    """
    Columns are lower level objects not meant to be manipulated
    by the user. Instead they are generated by Style classes the user
    configures or generates from a preset.
    """
    def __init__(self, fmt, style):

        # Set the format and strip leading/trailing whitespace.
        fmt = fmt.lstrip().rstrip()
        self.fmt = fmt
        self.style = style

        # Make a version of this format without any fmt_spec,
        # useful in figuring out text widths without ANSI characters.
        self.fmt_basic = re.sub(r'(?<=\w):\S+?(?=[\}:])', '', fmt)

        # Figure out the LogRecord fields present in this Column.
        self.fields = re.findall(r'(?<={)[a-zA-Z]+(?=[}:])', fmt)

        # Figure out if column is truncated.
        self.truncate_enabled = False
        if style.truncate_fields:
            for f in self.fields:
                if f in style.truncate_fields:
                    self.truncate_enabled = True

        # Figure out justification.
        self.justification = style.default_justification
        self.set_column_justification()

        # Figure out any adaptive length LogRecord fields.
        self.adaptive_fields = [x for x in self.fields
                                if x not in _fixed_length_fields]

        # Count any space used by the template string that
        # won't be formatted with a log record component
        self.reserved_padding = 0
        self.count_static_padding_amount()

        # Placeholder for the textwrap.TextWrapper instance
        # that will be used/reused in case of multiline breaks.
        self._wrapper = None

    ############################################################
    # Format tools
    ############################################################
    @staticmethod
    def return_simplified_format(fmt):
        """Take a given fmt and remove fmt_spec."""
        return re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)

    def return_field_from_format(self, fmt):
        s = self.return_simplified_format(fmt)
        return s[1:-1]

    ############################################################
    # Useful properties.
    ############################################################
    @property
    def wrapper(self):
        if not self._wrapper:
            self._wrapper = textwrap.TextWrapper(
                width=self.reserved_padding,
                break_long_words=True,
            )
        return self._wrapper

    ############################################################
    # Functions to figure out justification
    ############################################################
    def set_column_justification(self):
        """
        If required changes the Column.justify value
        to a non-defaults.
        Check multiple contageous properties have not been
        set in this column, and if so raise a warning.
        """
        justification_conf = self.style.justification_settings
        justification_override_dict = collections.OrderedDict()
        for field in justification_conf:
            if field in self.fields:
                justification_override_dict[field] = justification_conf[field]

        if justification_override_dict:
            if len(justification_override_dict) > 1:
                print('Warning: multiple contagious justifications '
                      f'specified for fields: {justification_override_dict}.'
                      f' Using first specified.')

            first_entry = justification_override_dict.popitem(last=False)[1]
            self.justification = first_entry

    ############################################################
    # Functions to take
    ############################################################
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
        contents_no_formats = re.sub(r'{\S+?}', '', self.fmt)
        self.reserved_padding += len(contents_no_formats)
        # If asctime is present add its length.
        if 'asctime' in self.fields:
            self.reserved_padding += self.style.datefmt_length
        # If levelname present add its length.
        if 'levelname' in self.fields:
            self.reserved_padding += self.style.max_levelname_length

    @property
    def empty_padding_string(self):
        """Empty padding string, to be used in multiline
        output where this column has no content."""
        return ' ' * self.reserved_padding

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
                    extra_padding = to_pad + len(line_fmt)
                    line_fmt = self.justification(line_fmt, extra_padding)
                s = line_fmt.format(**line_record_dict)
                formatted_lines.append(s)

                # If still fmt_to_parse, reset containers and increment
                # line index to get the new max length of the line.
                # Else we are done.
                if fmt_to_parse:
                    current_line_index += 1
                    this_line_max_length = line_length_map[current_line_index]
                    line_content = ''
                    line_fmt = ''
                    line_record_dict = {}

        return formatted_lines

    def justify_and_pad_input(self, record_dict):
        """
        Called when a line has been found to
        not use the full reserved padding, and
        so needs padded.
        """
        # Need the basic formatted content to know
        # how much to pad the format.
        fmt = self.fmt
        basic_content = self.fmt_basic.format(**record_dict)
        extra_room = self.reserved_padding - len(basic_content) + len(fmt)
        # Use the specified justify function to pad the format string.
        fmt = self.justification(fmt, extra_room)
        return fmt.format(**record_dict)

    def truncate_input(self, record_dict):
        """
        Truncate the format and content using the allotted space.

        Called when a line is too long to fit in the reserved padding
        and truncation is enabled for this column.
        """
        fmt_to_parse = self.fmt
        new_fmt = ''

        # Contains the output content as it is pushed back
        running_total_content = ''
        fitted_component_dict = {}

        # The allowed padding is the reserved padding minus the
        # length of the truncation chars
        allowed_padding = self.reserved_padding - self.style.truncation_chars_length
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
            partial_content = self.style.truncation_chars + partial_content
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
        """
        Return a string for the separator
        based on an input line number index (starting from zero).
        multiline-enabled separators always return the separators, otherwise
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

    def __init__(self, preset=None):
        """Inits the Style from a preset style name if given."""
        conf = copy.deepcopy(_style_defaults)
        if preset:
            try:
                conf.update(style_map[preset])
            except KeyError as e:
                print(f'Unknown style preset: {e}')
                raise
        self._conf = conf

        # At present only the strformat or "{" style is
        # supported in timbermafia.
        self._fmt_style = '{'

        # Placeholders for generated settings.
        self.generated_settings = {}
        self._column_dict = {}
        self._fields = []

    ############################################################
    # Info functions
    ############################################################
    def summarise(self):
        """Prints info on the current config."""
        print('- Current settings for style:')
        d = self._conf
        for config, value in d.items():
            if config == 'padding_weights':
                print(f'{config}:'.rjust(20))
                for k, v in value.items():
                    print(f'{k}:'.rjust(30), v)
                print()
            elif config == 'justify':
                print(f'{config}:'.rjust(20))
                for k, v in value.items():
                    print(f'{k}:'.rjust(30), _just_label_map[v])
            elif config == 'truncate_fields':
                print(f'{config}:'.rjust(20) + f' {",".join(value)}')
            else:
                print(f'{config}:'.rjust(20) + f' {value}')
        print('*'*50)

    ############################################################
    # Format properties.
    ############################################################
    @property
    def format_style(self):
        return self._fmt_style

    @property
    def format(self):
        """
        Get or set the format for the Formatter.

        timbermafia formats can support a fmt_spec and
        vertically aligned columns, e.g.
            {asctime:u} _ {levelname} _ {message:b}
        will produce an output with 3 vertically aligned columns with each
        log record component, with an underlined datetime and a bold message.

        The following are recognised in the format spec via a comma-separated
        list:
            b: bold
            e: emphasis/italic
            u: underline
            any int: the corresponding ANSI code, e.g. 5,9 will set slow blink
                     and crossed-out text
            >int: set the foreground colour to the 8-bit colour code, e.g. >34
                  for a bright green.
            <int: set the background colour to the 8-bit colour code.

        If a column escape is provided ("_" by default) then this books a
        vertically aligned column. The character immediately following this escape
        until any whitespace are the separator characters that will be printed.
        If whitespace immediately follows the escape, no separator character is
        printed.
        A single escape means any characters are printed on the first line of
        multi-line printout, double escape on all lines of multi-line output.
        e.g. the following format
            {asctime} _| {name}.{funcName} __>> {message}
        will produce output like
            11:44:13 | MyLog.my_function >> I am a very long message
                                         >> that is printed over several
                                         >> lines
        """
        return self._conf['format']

    @format.setter
    def format(self, f):
        # regex check needed here
        self._conf['format'] = f

    @property
    def datefmt_length(self):
        """Get the length in chars of the formatted date/time."""
        return len(time.strftime(self.datefmt))

    @property
    def datefmt(self):
        """Get or set the date/time format for the Formatter.

        This is the same as standard python logging.
        """
        return self._conf['datefmt']

    @datefmt.setter
    def datefmt(self, f):
        # regex check needed here
        self._conf['datefmt'] = f

    @property
    def column_escape(self):
        """Get or set the column escape character

        This character, by default "_", allows the user to specify
        vertically aligned columns in the format.
        """
        return self._conf['column_escape']

    @column_escape.setter
    def column_escape(self, v):
        if not isinstance(v, str) and len(v) == 1:
            raise ValueError('column_escape must be a single character')
        self._conf['column_escape'] = v

    ############################################################
    # Style behaviour settings
    ############################################################
    @staticmethod
    def _set_boolean(value):
        try:
            value = bool(value)
            return value
        except ValueError:
            raise

    @property
    def colourised_levels(self):
        """Get or set the flag for colourised output dependent on log level."""
        return self._conf['colourised_levels']

    @colourised_levels.setter
    def colourised_levels(self, value):
        self._conf['colourised_levels'] = self._set_boolean(value)

    @property
    def short_levels(self):
        """Get or set the short levels flag.

        If True, log level names will be abbreviated,
        for example INFO -> I, DEBUG -> D.
        """
        return self._conf['short_levels']

    @short_levels.setter
    def short_levels(self, value):
        self._conf['short_levels'] = self._set_boolean(value)

    @property
    def clean_output(self):
        """Get or set the output cleaning flag.

        If true, removes the following redundant substrings from output:
        - "root." from logger names
        """
        return self._conf['clean_output']

    @clean_output.setter
    def clean_output(self, value):
        self._conf['clean_output'] = self._set_boolean(value)

    ############################################################
    # Width and fit_to_terminal options
    ############################################################
    @property
    def width(self):
        """Get or set the width in characters of the output."""
        return self._conf['width']

    @width.setter
    def width(self, value):
        try:
            value = int(value)
        except ValueError:
            raise
        self._conf['width'] = value

    @property
    def fit_to_terminal(self):
        """Get or set the flag to fit to terminal.

        If True, each time the Formatter has to process output, it
        will check the current terminal width if applicable, and
        adjust the total width accordingly.

        If a max width is specified in the style it is respected.
        """
        return self._conf['fit_to_terminal']

    @fit_to_terminal.setter
    def fit_to_terminal(self, value):
        self._conf['fit_to_terminal'] = self._set_boolean(value)

    @property
    def use_max_width(self):
        """Check a valid max width is set, and if not ignore it."""
        if not self._conf['max_width']:
            return False
        return True

    @property
    def max_width(self):
        """Get or set a maximum width for the output.

        Useful when fit to terminal is also being used.
        If set to something that evaluates as False, is ignored.

        Widths below 40 characters raise a ValueError because such low
        widths perform poorly.
        """
        return self._conf['max_width']

    @max_width.setter
    def max_width(self, i):
        # Allow false or None values to be used
        if i is None or i is False:
            self._conf['max_width'] = False
        # Else try to cast the int and ensure it's over 40
        try:
            i = int(i)
        except ValueError:
            raise
        # timbermafia tends to break below 40 chars
        if i < 40:
            raise ValueError('max_width: {i} is too low,'
                             ' must be above 40.')
        self._conf['max_width'] = i

    ############################################################
    # Justification properties and funcs
    ############################################################
    def set_justification(self, key, value):
        """Function to set an individual log record field's justification

        Args:
            key: the log record field, e.g. "name", "message"
            value: should be either
                - a string in ['l', 'r', 'c', 'left', 'right', 'center']
                - a func in [str.ljust, str.rjust, str.center]
        """
        # If we get a string matching the key:
        if isinstance(value, str) and value in _just_functions_map:
            self._conf['justify'][key] = _just_functions_map[value]
        # Else if given a function that is in the dict values, use it.
        elif value in _just_functions_map.values():
            self._conf['justify'][key] = value
        # Else not recognised, raise Exception
        else:
            msg1 = (f'justify arg must be a string in:'
                    f' {",".join(_just_functions_map.keys())}')
            valid_funcs = list(set(_just_functions_map.values()))
            msg2 = f' or a func in {",".join(valid_funcs)}'
            raise ValueError(msg1+msg2)

    @property
    def justification_settings(self):
        return self._conf['justify']

    @property
    def default_justification(self):
        """Get or set the default justification function for the style."""
        return self._conf['justify']['default']

    @default_justification.setter
    def default_justification(self, v):
        self.set_justification('default', v)

    ############################################################
    # Adaptive padding properties and funcs
    ############################################################
    def set_weight(self, field, value):
        """Set a relative weight for a log record field's padding.

        Weights determine the allotted width of any fields
        that have a non-deterministic padding, e.g. function names,
        messages, log names.

        If a field does not have a weight it uses the default
        weight for the style.
        Weights for fields in a given column are additive.

        Args:
            field: the log record field.
            value: a number indicating the relative weight.
        """
        try:
            value = float(value)
            field = str(field)
        except ValueError:
            raise
        self._conf['padding_weights'][field] = value

    @property
    def default_weight(self):
        """Get or set the default weight for log record field padding."""
        return self._conf['padding_weights']['default']

    @default_weight.setter
    def default_weight(self, value):
        self.set_weight('default', value)

    ############################################################
    # Truncation properties and funcs
    ############################################################
    @property
    def truncate_fields(self):
        """Get or set the log record fields to truncate.

        The argument can be a single field or a list of fields.

        Truncation is a contagious property, so if one field
        in a given column is marked for truncation, the whole
        column is truncated.

        In truncation, the start of the string is pruned until
        the string fits in a single line of the allotted width,
        with the truncation characters prepended.
        """
        return self._conf['truncate_fields']

    @truncate_fields.setter
    def truncate_fields(self, fields):
        if isinstance(fields, str):
            self._conf['truncate_fields'] = [fields]
        elif isinstance(collections.abc.Sequence, fields):
            self._conf['truncate_fields'] = [fields]
        else:
            raise ValueError(f'fields: {fields} not a string or iterable.')

    @property
    def truncation_chars(self):
        """Get or set the truncation characters for this style."""
        return self._conf['truncation_chars']

    @truncation_chars.setter
    def truncation_chars(self, value):
        try:
            value = str(value)
        except ValueError:
            print('truncation_chars must be a string')
            raise
        self._conf['truncation_chars'] = value

    @property
    def truncation_chars_length(self):
        return len(self.truncation_chars)

    def truncate_field(self, field):
        """Register an individual field for truncation."""
        if field not in self._conf['truncate_fields']:
            self._conf['truncate_fields'].append(field)

    ############################################################
    # Read-only properties used frequently in the code
    ############################################################
    @property
    def max_levelname_length(self):
        """Gets the character length of the maximum level name."""
        if self.short_levels:
            return 1
        return len(max(logging._nameToLevel.keys(), key=len))

    @property
    def simple_format(self):
        """Return the format without any unnecessary whitespace or fmt_specs."""
        fmt = self.format
        fmt = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        fmt = re.sub(self.column_escape, '', fmt)
        return fmt

    @property
    def no_ansi_log_format(self):
        """Return the format without any fmt_spec, but maintain
        the column separators.
        """
        fmt = self.format
        fmt = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        return fmt

    @property
    def width_to_use(self):
        """Return the full width of the log output.

        Depends on fit_to_terminal and max_width settings.
        """
        if self.fit_to_terminal:
            i = shutil.get_terminal_size().columns
            if self.use_max_width:
                if i > self.max_width:
                    return self.max_width
            return i
        # If no adaptive settings return the simple width.
        else:
            return self.width

    @property
    def fields(self):
        """Return a list of all fields used in the Style's format"""
        if not self._column_dict:
            self.generate_column_settings()
        if self._fields is None:
            self._fields = [
                x for y in list(c.fields for c
                                in self._column_dict.values())
                for x in y
            ]
        return self._fields

    ############################################################
    # Functions to generate columns and separators for this
    # style and format.
    ############################################################
    def _calculate_padding(self, column_dict, separator_dict, template):
        """Function to evaluate column padding widths."""
        # Get the total reserved space from each column,
        # which does not account for any adaptive
        # length record components.
        total_used_space = sum([c.reserved_padding for c
                                in column_dict.values()])

        # Add spaces from the template
        non_special_chars = ''.join(
            [s for s in re.findall(r'(.*?){.*?}', template) if s]
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
        space_for_adaptive = self.width_to_use - total_used_space
        if space_for_adaptive < 5:
            raise ValueError('Insufficient space for this configuration.'
                             ' Specify a higher width.')
        adaptive_fields_dict = {}
        weights = self._conf['padding_weights']

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
        deficit = self.width_to_use - all_column_padding - separator_padding - nsp_len
        while deficit > 0:
            for c in column_dict.values():
                if c.adaptive_fields:
                    c.reserved_padding += 1
                    deficit -= 1
                    if deficit == 0:
                        break

    def generate_column_settings(self):
        """Function to parse the log format to understand any column
        and separator specification, and return the information
        in a dict.
        """
        # Reset recorded settings from any possible previous configs.
        self._fields = None

        fmt = self.format
        # Remove any escaped formatters from the format
        # and replace them with the escape character
        # for easy splitting of column-specific formats.
        fmt_no_separators = re.sub(utils.column_sep_pattern,
                                   self.column_escape, fmt)
        all_column_formats = fmt_no_separators.split(self.column_escape)

        # Only consider parts of the format if they contain
        # at least one LogRecord field.
        formats_with_fields = [
            fmt for fmt in all_column_formats if
            utils.logrecord_present_pattern.match(fmt)
        ]

        # Generate the required Column objects.
        # The Style class contains all the info the columns need,
        # so just pass a reference to it.
        # Info is stored in a dict with uppercase character keys.
        column_dict = {
            k: Column(fmt, self)
            for k, fmt in zip(string.ascii_uppercase, formats_with_fields)
        }

        # Generate the Separator objects.
        # Info is stored in a dict with lowercase character keys.
        separators = re.findall(utils.column_sep_pattern, fmt)
        separator_dict = {
            k: Separator(sep, self.column_escape) for k, sep in
            zip(string.ascii_lowercase, separators)
        }

        # Create a template for the fully-formatted separator and column
        # content to be subbed back into.
        # Do this sequentially in case of identical fields or separators.
        template = fmt
        # Columns.
        for key, c in column_dict.items():
            template = template.replace(c.fmt, '{' + key + '}', 1)

        # Separators
        for key, s in separator_dict.items():
            template = template.replace(s.content, '{' + key + '}', 1)

        # Any fixed reserved padding has been calculated for each column
        # Now take the ensemble of columns and establish what adaptive
        # fields are present in each, and delegate additional padding to
        # these columns based on the field's padding weight.
        self._calculate_padding(column_dict, separator_dict, template)

        # Internally assign these attributes.
        self._column_dict = column_dict

        d = {
            'columns': column_dict,
            'separators': separator_dict,
            'template': template
        }
        self.generated_settings = d
