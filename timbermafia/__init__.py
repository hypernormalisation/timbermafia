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

STYLES = {
    'minimalist': {
        'default_format': '{asctime} _ {message}',
    }
}

STYLE_DEFAULTS = {
    'smart_names': True,
    'justify': {
        'default': str.rjust,
        'left': ['message']
        },
    'time_format': '%H:%M:%S',
    'padding': {
        'default': 0.2,
        'message': 0.8,
        # 'name': 0.15,
        # 'funcName': 0.15,
    },
    'truncate': ['name'],
    'log_format': '{asctime:u} _| {levelname} _| {name}.{funcName} __>> {message:b,>118}',
    'column_escape': '_',
    'format_style': '{',
    'fit_to_terminal': False,
    'n_columns': 100,
}


class Column:

    def __init__(self, fmt):
        self.fmt = fmt
        self.fmt_stripped = fmt.lstrip().rstrip()
        self.fmt_basic = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        self.fields = re.findall(r'(?<=\{)[a-zA-Z]+(?=[\}:])', fmt)
        # print(self.__dict__)

    def __str__(self):
        return 'Column({})'.format(self.fmt)


class Separator:
    def __init__(self, content, column_escape):
        self.content = content
        self.column_escape = column_escape
        self.content_escaped = content.replace(column_escape, '')
        self.len = len(self.content_escaped)
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

        # Explicitly set the properties a logging.Formatter object
        # expects that need custom verification
        self.format_style = kwargs.get('format_style', conf['format_style'])
        self.log_format = kwargs.get('log_format', conf['log_format'])
        self.time_format = kwargs.get('time_format', conf['time_format'])

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

    @property
    def time_format_length(self):
        """Returns the length in chars of the asctime
        with the current time format"""
        return len(time.strftime(self.time_format))

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

    def calculate_padding(self, column_dict, separator_dict, template):
        """Function to evaluate column padding widths"""

        # Iterate over the column dict as a first pass
        # to determine the presence of fixed and adaptive
        # length fields.
        for k, v in column_dict.items():
            used_padding = 0
            adaptive_fields = []
            contents = v['contents']

            # Add the space in this segment not dedicated to
            # log record components
            contents_no_formats = re.sub(r'\{\S+?\}', '', contents)
            used_padding += len(contents_no_formats)
            # print('No formats "'+contents_no_formats+'"')
            # print(k, v['fields'])

            # Iter over fields in this segment to get
            # fixed and adaptive fields.
            for f in v['fields']:
                if f == 'levelname':
                    used_padding += self.max_levelname_length
                elif f == 'asctime':
                    used_padding += self.time_format_length
                # On the first pass note the adaptive elements.
                else:
                    adaptive_fields.append(f)
            v['used_padding'] = used_padding
            v['adaptive_fields'] = adaptive_fields

        # print(column_dict)

        total_used_space = sum([v['used_padding'] for v
                                in column_dict.values()])

        # Add spaces from the template
        # ws = [i for i in template if i.is]
        non_special_chars = [s for s in
                             re.findall(r'(.*?)\{.*?\}', template) if s]
        # print(len(non_special_chars))
        # total_used_space += len(non_special_chars)

        # Add space used on separators
        separator_padding = 0
        for k, v in separator_dict.items():
            separator_padding += v['len']
        total_used_space += separator_padding
        # print(total_used_space)

        adaptive_fields = [
            x for y in list(v['adaptive_fields'] for v
                            in column_dict.values())
            for x in y
        ]

        # print(adaptive_fields)

        # Normalise adaptive fields to space left
        space_for_adaptive = self.n_columns - total_used_space
        # print('space remaining', space_for_adaptive)

        adaptive_fields_dict = {}
        weights = self.conf['padding']

        for i, f in enumerate(adaptive_fields):
            weight = weights.get(f, weights['default'])
            adaptive_fields_dict[i] = {'field': f, 'weight': weight}

        # print(adaptive_fields_dict)

        total_weights = sum(v['weight'] for v in adaptive_fields_dict.values())
        # print(total_weights)
        for v in adaptive_fields_dict.values():
            v['char_length'] = math.floor(
                (v['weight'] / total_weights) * space_for_adaptive
            )
        # print(adaptive_fields_dict)

        ad2 = {}
        for v in adaptive_fields_dict.values():
            f = v['field']
            if f not in ad2:
                ad2[f] = v['char_length']

        # print(ad2)

        # We've used floors so might have multiple chars to spare.
        # Consider incrementing the message char_length here if the sum
        # is below the space_for_adaptive

        test_padding = 0
        for k, v in column_dict.items():
            for f in v['adaptive_fields']:
                char_length = ad2[f]
                v['used_padding'] += char_length
            test_padding += v['used_padding']

        # print(test_padding, separator_padding)

        # Indicate for each column if multiline spillover is a
        # possibility to make Formatter checks quicker.
        # This is only possible if there are adaptive fields present,
        # and none of them are in the truncate setting.
        for v in column_dict.values():
            truncate = False
            a = v['adaptive_fields']
            if a:
                for field in a:
                    if field in self.conf['truncate']:
                        truncate = True
            if a and not truncate:
                v['can_be_multiline'] = True
            else:
                v['can_be_multiline'] = False

        deficit = self.n_columns - test_padding - separator_padding

    def append_column_justifications(self, column_dict):
        """Method to take the column dict created by generate_column_settings
        and insert column-wide settings like justification."""
        just_conf = self.conf['justify']
        default = just_conf['default']
        to_ljust = just_conf.get('left', [])
        to_rjust = just_conf.get('right', [])
        to_cjust = just_conf.get('center', [])

        for d in column_dict.values():
            fields = d['fields']
            override = False
            for field in fields:
                # print(field)
                if field in to_ljust:
                    d['justify'] = str.ljust
                    override = True
                    continue
                if field in to_rjust:
                    override = True
                    d['justify'] = str.rjust
                    continue
                if field in to_cjust:
                    override = True
                    d['justify'] = str.center
                    continue
            # If no fields have a value use the default
            if not override:
                d['justify'] = default
        # print(column_dict)

    def generate_column_settings(self):
        """
        Function to parse the log format to understand any column
        and separator specification, and return the information
        in a dict.
        """
        # Log segments with fmt_spec
        fmt = self.log_format
        partial_text = re.sub(utils.column_sep_pattern,
                              self.column_escape, fmt)
        parts = partial_text.split(self.column_escape)

        # Non-fmt_spec templates
        # fmt_basic = self.no_ansi_log_format
        # partial_text_basic = re.sub(utils.column_sep_pattern,
        #                             self.column_escape, fmt_basic)
        # parts_basic = partial_text.split(self.column_escape)

        column_dict = {k: Column(v) for k, v
                       in zip(string.ascii_uppercase, parts)}
        # print(column_dict)

        # column_dict = {k: {
        #     'contents': v.lstrip().rstrip(),
        #     'contents_basic': x.lstrip().rstrip()
        #     }
        #     for k, v, x in zip(string.ascii_uppercase, parts, parts_basic)
        #     if re.match(utils.logrecord_present_pattern, v)
        # }
        #
        # for c in column_dict2.values():
        #     s = c.fmt
        #     d['fields'] = re.findall(r'(?<=\{)[a-zA-Z]+(?=[\}:])', s)

        # Create a template for the formatted separators and columns
        # to go into.

        template = fmt
        for key, c in column_dict.items():
            template = template.replace(c.fmt_stripped,
                                        '{'+key+'}')
        # print(template)

        separators = re.findall(utils.column_sep_pattern, fmt)
        # print(separators)
        # separator_dict = {}
        separator_dict = {
            k: Separator(sep, self.column_escape) for k, sep in
            zip(string.ascii_lowercase, separators)
        }
        # print(separator_dict)
        # for sep, a in zip(separators, string.ascii_lowercase):
        #     unescaped = sep.replace(self.column_escape, '')
        #     d = {
        #         'original_content': sep,
        #         'contents': unescaped,
        #         'len': len(unescaped),
        #         'multiline': '__' in sep,
        #     }
        #     separator_dict[a] = d

        # Now substitute the separators sequentially in case of
        # identical separators.
        for key, s in separator_dict.items():
            template = template.replace(s.content, '{'+key+'}', 1)

        print(column_dict)
        print(separator_dict)
        print(template)
        self.append_column_justifications(column_dict)
        self.calculate_padding(column_dict, separator_dict, template)

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
