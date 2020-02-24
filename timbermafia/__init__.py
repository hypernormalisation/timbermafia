import logging
import shutil
import copy
# from logging import root
from timbermafia.rainbow import RainbowStreamHandler, RainbowFileHandler, palette_dict
from timbermafia.formatters import TMFormatter
from timbermafia.utils import *
from collections.abc import Iterable

log = logging.getLogger(__name__)

_valid_for_bools = [0, 1, True, False]
_valid_formatters = ['default']
_valid_palettes = list(palette_dict.keys())
_valid_configs = {
    'formatter': _valid_formatters,
    'palette': _valid_palettes,
    'monochrome': _valid_for_bools,
    'bold': _valid_for_bools,
    'enclose': _valid_for_bools,
    'show_separator': _valid_for_bools,
    'justify': ['left', 'right', 'center'],
    'style': ['{'],
}

t_size = shutil.get_terminal_size()

# Defaults for timbermafia.config
_config = {
    # Handler settings
    'level': logging.DEBUG,

    # Preset styles and settings
    'formatter': 'default',
    'palette': 'sensible',
    'monochrome': False,
    'bold': True,
    'enclose': True,
    'justify': 'right',
    'justify_left': ['message'],
    'justify_right': [],
    'justify_center': [],
    'show_separator': True,

    # Column and padding widths
    'columns': t_size.columns,
    'name_padding': 10,
    'funcName_padding': 13,
    'module_padding': 25,
    'pathname_padding': 40,
    'lineNo_padding': 4,
    'thread_padding': 4,
    'threadName_padding': 10,

    # Default formats
    'format': '{asctime} | {name}.{funcName} | {message}',
    'time_format': '%H:%M:%S',
    'style': '{',
    'separator': '|',
    'truncate': ['funcName'],
}

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
    temp_dict = {}
    check_kwargs(kwargs, 'configure')
    for key, val in kwargs.items():
        temp_dict[key] = val
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
                            config=c, style=c['style'])

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
