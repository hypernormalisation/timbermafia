import logging
# import shutil
import re
import string
import sys
import timbermafia.formats
from timbermafia.rainbow import RainbowStreamHandler, RainbowFileHandler, palette_dict
from timbermafia.formatters import TimbermafiaFormatter
import timbermafia.utils as utils

# from timbermafia.utils import *

log = logging.getLogger(__name__)

# t_size = shutil.get_terminal_size()

# left = str.ljust
# right = str.rjust
# center = str.center


STYLES = {
    'minimalist': {
        'default_format': '{asctime} _ {message}',
    }
}

STYLE_DEFAULTS = {
    'smart_names': True,
    'justify': {
        'default': str.rjust,
        'left_fields': ['message']
        },
    'time_format': '%H:%M:%S',
    'padding': {},
    'log_format': '{asctime:u} _| {name}.{funcName} __>> {message:b,>118}',
    'column_escape': '_',
    'format_style': '{',
}


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
        return None

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

    def generate_column_settings(self):
        """
        Function to parse the log format to understand any column
        and separator specification, and return the information
        in a dict.
        """
        fmt = self.log_format
        partial_text = re.sub(utils.column_sep_pattern,
                              self.column_escape, fmt)
        # print(partial_text)

        parts = partial_text.split(self.column_escape)
        column_dict = {k: {'contents': v} for k, v in enumerate(parts)
                       if re.match(utils.logrecord_present_pattern, v)}

        for k, d in column_dict.items():
            s = d['contents']
            d['fields'] = re.findall(r'(?<=\{)[a-zA-Z]+(?=[\}:])', s)

        template = fmt
        for i, d in column_dict.items():
            s = d['contents']
            template = template.replace(s, '{'+str(i)+'}')
        # print(template)

        separators = re.findall(utils.column_sep_pattern, fmt)
        # print(separators)
        separator_dict = {}
        for sep, a in zip(separators, string.ascii_lowercase):
            unescaped = sep.replace(self.column_escape, '')
            d = {
                'original_content': sep,
                'contents': unescaped,
                'len': len(unescaped),
                'multiline': '__' in sep,
            }
            separator_dict[a] = d

        # Now substitute the separators
        for sep, d in separator_dict.items():
            # print(sep)
            template = template.replace(d['original_content'], '{'+sep+'}', 1)

        # print(column_dict)
        # print(separator_dict)
        # print(template)
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
