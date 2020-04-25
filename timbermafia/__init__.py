import logging
import shutil
import copy
import inspect
import sys
import timbermafia.formats
from timbermafia.rainbow import RainbowStreamHandler, RainbowFileHandler, palette_dict
from timbermafia.formatters import TMFormatter2
from timbermafia.utils import *
from collections.abc import Iterable

log = logging.getLogger(__name__)

t_size = shutil.get_terminal_size()

left = str.ljust
right = str.rjust
center = str.center


style_dict = {
    'minimalist': {
        'default_format': '{asctime} _ {message}',
    }
}


class Style:
    """Class to hold style settings used in timbermafia
    logging subclasses."""
    default = {
        'smart_names': True,
        'justify': {'default': right, 'left_fields': ['message']},
        'time_format': '%H:%M:%S',
        'padding': {},
        'default_format': '{asctime:u} _| {name}.{funcName} __>> {message:>15}',
        'column_escape': '_',
    }

    def __init__(self, preset=None, fmt=None):
        self.conf = self.default
        self._fmt = fmt
        if preset:
            self.conf.update(style_dict[preset])
        self.validate_format()

    @property
    def format(self):
        if not self._fmt:
            return self.conf['default_format']
        return self._fmt

    @format.setter
    def format(self, f):
        # Put a regex here to ensure the format is valid.
        self._fmt = f

    @property
    def column_escape(self):
        return self.conf['column_escape']

    @property
    def simple_format(self):
        """Return the format without any unnecessary whitespace or fmt_spec"""
        fmt = self.format
        fmt = re.sub(r'(?<=\w):\S+(?=[\}:])', '', fmt)
        fmt = re.sub(self.column_escape, '', fmt)
        return fmt

    def validate_format(self):
        """Validate the format for this style to ensure timbermafia
        can properly parse it"""
        pass


def basic_config(
        style=None, fmt=None, stream=sys.stdout, filename=None,
        clear=False, basic_files=True, handlers=None,
        ):
    """Function for basic configuration of timbermafia logging.

    Describe Args here
    """
    logging._acquireLock()  # don't like that this is protected

    try:
        # Reference to the root logger
        logger = logging.root

        # Reset handlers on request
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
            custom_formatter = TMFormatter2(style=my_style)

        use_default_formatter = filename and not basic_files
        if use_default_formatter:
            # In line below we'll add the basic format from the style property
            default_formatter = logging.Formatter(my_style.simple_format)

        # Add streamhandler if specified
        if stream:
            h = RainbowStreamHandler()
            h.setFormatter(custom_formatter)
            handlers.append(h)

        if filename:
            h = logging.FileHandler(filename)
            if basic_files:
                h.setFormatter(default_formatter)
            else:
                h.setFormatter(custom_formatter)

        for h in handlers:
            logger.addHandler(h)

    finally:
        logging._releaseLock()  # again don't like this




# def add_handler(style=None, format=None,
#                 stream=sys.stdout, filename=None,
#                 clear=False, simple_files=True, handlers=None):
#     # s = tm.generate_style_from_template('minimalist')
#     # s.change_something
#     # tm.configure(style='minimalist')
#
#     # Generate style
#     my_style = Style(preset=style, format=format)
#
#     # Figure out handlers
#     handler_list = []
#     if stream:
#         h = RainbowStreamHandler(# args here)
#         handler_list.append(h)
#     if filename:
#         if simple_files:
#             h = logging.FileHandler( # args here)
#         else:
#             h = RainbowFileHandler( # args here )
#     if handlers:
#         for h in handlers:
#             if isinstance(h, logging.FileHandler):
#                 if simple_files:


# A dict of settings for predetermined styles
#
# style_dict = {
#     'default':
# }
#     'default': {},
#         'format': '{1} _| {2} __>> | {3}',
#         '1': Column('{asctime}'),
#         '2': Column('{name}.{funcName}'),
#         '3': Column('{message}', justify=left),
#     }


# # Styles with preset configs
# style_map = {
#     'default': {},
#     'simple': {
#         'format': '{name}.{funcName} > {message}',
#         'separator': '>',
#         'show_separator': True,
#         'sparse_separator': True,
#         'enclose': False,
#         'truncate': [],
#         # 'truncate': ['name'],
#         'name_padding': 8,
#         'funcName_padding': 8,
#         'justify': 'left',
#         'justify_right': [],
#         'line_separator': '-',
#     },
#     'minimalist': {
#         'show_separator': False,
#         'sparse_separators': False,
#         'enclose': False,
#         'format': '{asctime} | {name}.{funcName} | {message}',
#         'truncate': [],
#         'name_padding': 10,
#         'funcName_padding': 10,
#         'columns': int(t_size.columns * 1.),
#     },
#     'boxed': {
#         'enclose': True,
#         'time_format': "%H:%M:%S",
#         'format': '{asctime} | {levelname} | {name}.{funcName} | {message}',
#         'show_separator': True,
#         'divide_lines': True,
#         'truncate': [],
#         'line_separator': '=',
#         'sparse_separators': False,
#     },
#     'jupyter': {
#         'bold': False,
#         'show_separator': False,
#         'enclose': False,
#         'format': '{asctime} | {name}.{funcName} | {message}',
#     },
#     'doublespace': {
#         'line_separator': ' ',
#         'divide_lines': True,
#         'sparse_separators': True,
#         'enclose': False,
#     }
# }
#
# # Add monochrome styles
# mono_styles = {}
# for style in style_map:
#     d = copy.deepcopy(style_map[style])
#     d['monochrome'] = True
#     mono_styles[f'{style}_mono'] = d
# style_map.update(mono_styles)
#
# style_map['minimalist_mono']['format'] = '{asctime} | {levelname} | {name}.{funcName} | {message}'
# style_map['simple_mono']['format'] = '{levelname} > {name}.{funcName} > {message}'

# _valid_for_bools = [0, 1, True, False]
# _valid_palettes = list(palette_dict.keys())
# _valid_configs = {
#     'palette': _valid_palettes,
#     'monochrome': _valid_for_bools,
#     'bold': _valid_for_bools,
#     'enclose': _valid_for_bools,
#     'show_separator': _valid_for_bools,
#     'divide_lines': _valid_for_bools,
#     'clean_names': _valid_for_bools,
#     'sparse_separators': _valid_for_bools,
#     'justify': ['left', 'right', 'center'],
#     'separator_style': ['basic', 'smart', 'full'],
#     'format_style': ['{'],
#     'style': style_map.keys(),
# }



# Defaults for timbermafia.config
_config = {
    # Handler settings
    'level': logging.DEBUG,

    # Preset styles and settings
    'style': 'default',
    'palette': 'sensible',
    'monochrome': False,
    'bold': True,
    'enclose': False,
    'enclosers': [],
    'show_separator': True,
    'divide_lines': False,
    'line_separator': '~',
    'separator': '|',
    'separator_style': 'smart',
    'sparse_separators': True,
    'sparse_fields': ['message'],
    'clean_names': True,

    # Justification options
    'justify': 'right',
    'justify_left': ['message'],
    'justify_right': [],
    'justify_center': [],
    'truncate': ['funcName'],

    # Column and padding widths
    'columns': t_size.columns,
    'name_padding': 10,
    'funcName_padding': 10,
    'module_padding': 25,
    'pathname_padding': 40,
    'lineNo_padding': 4,
    'thread_padding': 15,
    'threadName_padding': 10,

    # Default formats
    'format': '{asctime} | {levelname} | {name}.{funcName} | {message}',
    'time_format': '%H:%M:%S',
    'format_style': '{',  # this is what logging calls "style"
}

_default_conf = copy.deepcopy(_config)

# Defaults for add_handler
_config2 = {
    'filename': None,
    'stream': None,
    'log_name': None,
    'level': logging.DEBUG,
    'handlers': None,
    'clear': False,
    'enhance_logger': True,
}


def check_kwargs(kwargs, func_name):
    """Function to check arguments for configuration."""
    c = None
    if func_name == 'configure':
        c = _config
    elif func_name == 'add_handler':
        c = _config2
    for key, val in kwargs.items():
        if key in c:
            # If only pre-set configs allowed, check them
            if key in _valid_configs:
                if val not in _valid_configs[key]:
                    vcs = [str(x) for x in _valid_configs[key]]
                    s = f'Value for {key}: {val}, must be ' \
                        f'one of {", ".join(vcs)}'
                    raise ValueError(s)
        # Intercept unknown args
        else:
            raise ValueError(f'Unknown argument: {key}')


def configure(**kwargs):
    """The user interface to setting timbermafia configuration."""
    check_kwargs(kwargs, 'configure')
    temp_dict = {}

    # Get the style first if given, so we can reset the config
    # and the user can customise styles easily.
    style = kwargs.get('style')
    if style:
        _config.update(_default_conf)
        for setting, value in style_map[style].items():
            temp_dict[setting] = value

    # Each time configure is called, recheck the padding.
    columns = kwargs.get('columns', shutil.get_terminal_size().columns)
    temp_dict['columns'] = columns

    for key, val in kwargs.items():
        temp_dict[key] = val

    # Check for inconsistent settings
    justification_dict = {}
    justification_dict.update(_config)
    justification_dict.update(temp_dict)
    just_lr = [x for x in justification_dict['justify_left']
               if x in justification_dict['justify_right']]
    just_lc = [x for x in justification_dict['justify_center']
               if x in justification_dict['justify_left']]
    just_rc = [x for x in justification_dict['justify_center']
               if x in justification_dict['justify_right']]
    print(justification_dict)
    if just_lr or just_lc or just_rc:
        justs = just_rc + just_lc + just_lr
        raise ValueError('Multiple justifications specified for '
                         'section : '+', '.join(justs))

    _config.update(temp_dict)


def enhance(l):
    """Function to add a header function to the Logger class."""
    def timbermafia_header_04ce0a20e181(self, msg):
        self.info(divider())
        self.info(msg)
        self.info(divider())
    l.header = timbermafia_header_04ce0a20e181


def add_handler(**kwargs):
    """
    Configure one or more handlers.
    """
    check_kwargs(kwargs, 'add_handler')
    c = copy.deepcopy(_config)

    formatter = TMFormatter(c['format'], c['time_format'],
                            config=c, style=c['format_style'])

    user_formatter = kwargs.get('formatter')
    if user_formatter:
        if not isinstance(user_formatter, logging.Formatter):
            raise ValueError('formatter must be a '
                             'logging.Formatter based object')
        formatter = user_formatter

    ###################################################################################
    # Configure handlers
    ###################################################################################
    handlers = []

    # If given get user handlers
    user_handlers = kwargs.get('handlers', _config2['handlers'])
    if user_handlers:
        if not isinstance(user_handlers, Iterable):
            user_handlers = [user_handlers]
        for h in user_handlers:
            if not isinstance(h, logging.Handler):
                raise ValueError('handlers must be a logging.Handler object or iterable'
                                 'of logging.Handler objects')
            h.setFormatter(formatter)
            handlers.append(h)

    # Log level
    level = kwargs.get('level', _config['level'])

    # Configure stream handler if required.
    stream = kwargs.get('stream', _config2['stream'])
    if stream:
        if not _config['monochrome']:
            s = RainbowStreamHandler(stream=stream,
                                     config=c)
        else:
            s = logging.StreamHandler(stream=stream)
        s.setFormatter(formatter)
        handlers.append(s)

    # Configure file handler if required.
    filename = kwargs.get('filename', _config2['filename'])
    if filename:
        if not _config['monochrome']:
            f = RainbowFileHandler(filename, config=c)
        else:
            f = logging.FileHandler(filename)
        f.setFormatter(formatter)
        handlers.append(f)

    ###################################################################################
    # Logger config
    ###################################################################################
    log_name = kwargs.get('log_name', _config2['log_name'])
    l = logging.getLogger(log_name)

    # Reset handlers on request
    clear = kwargs.get('clear', _config2['clear'])
    if clear:
        for h in l.handlers[:]:
            l.removeHandler(h)
            h.close()

    for h in handlers:
        h.setLevel(level)
        l.addHandler(h)

    # Set level
    l.setLevel(level)

    # Enhance the Logger class
    enhance_logger = kwargs.get('enhance_logger', _config2['enhance_logger'])
    if enhance_logger and not hasattr(logging.Logger, 'header'):
        enhance(logging.Logger)


class Logged:
    """
    Inherit from this class to provide a mixin logger via
    the log property.
    """
    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'root.{self.__class__.__name__}')
