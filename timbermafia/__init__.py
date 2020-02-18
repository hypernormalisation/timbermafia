import inspect
import logging
import sys
import textwrap
import functools
from logging import root
from timbermafia.rainbow import RainbowStreamHandler, palette_dict
from timbermafia.formatters import TMFormatter
from timbermafia.utils import *

log = logging.getLogger(__name__)

_valid_styles = ['default', 'test1']
_valid_palettes = list(palette_dict.keys())

_valid_configs = {
    'timbermafia_style': _valid_styles,
    'palette': _valid_palettes,
    'monochrome': [0, 1, True, False],
}

_config = {
    # Handler settings
    'stream': sys.stdout,
    'filename': None,
    'level': logging.DEBUG,

    # Preset styles
    'timbermafia_style': 'default',
    'palette': 'neon',
    'monochrome': False,

    # Column and padding widths
    'columns': 120,
    'name_padding': 12,
    'funcName_padding': 13,
    # 'caller_padding': 25,
    'module_padding': 25,
    'pathname_padding': 40,
    'lineNo_padding': 4,
    'thread_padding': 4,
    'threadName_padding': 10,

    # Default formats
    'format': '{asctime} | {name}.{funcName} | {message}',
    'file_format': '{asctime} | {levelname} | {name}.{funcName} | {message}',
    'time_format': '%H:%M:%S',
    'style': '{',
    'separator': '|',
}


def set_config(**kwargs):
    temp_dict = {}
    for key, val in kwargs.items():
        if key in _config:

            # If only pre-set configs allowed, check them
            if key in _valid_configs:
                if val not in _valid_configs[key]:
                    s = f'Value for {key}: {val}, must be ' \
                        f'one of {", ".join(_valid_configs[key])}'
                    raise ValueError(s)

            temp_dict[key] = val

        # Intercept unknown args
        else:
            raise AttributeError(f'Unknown argument {key}')

    # Check the config is valid.
    columns = temp_dict.get('columns', _config.get('columns'))
    caller_padding = temp_dict.get('caller_padding', _config.get('caller_padding'))
    if columns < caller_padding:
        raise ValueError(f'Width ({columns}) must be greater'
                         f' than caller padding ({caller_padding}')

    # Update
    _config.update(temp_dict)


def enhance(log):
    levels = []
    for level_name in logging._nameToLevel.keys():
        if level_name != 'NOTSET':
            levels.append(level_name.lower())
    levels = set(levels)
    funcs = [getattr(root, level) for level in levels]
    for func, level in zip(funcs, levels):
        setattr(log, f'h{level}', headed_log(func=func))


def configure_root_logger(**kwargs):
    """Function to configure the root logger in logging, as for logging.basicConfig"""
    # Reset handlers
    force = kwargs.get('force', True)
    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)
            h.close()

    stream_formatter = TMFormatter(_config['format'], _config['time_format'],
                                   config=_config, style=_config['style'])
    file_formatter = TMFormatter(_config['file_format'], _config['time_format'],
                                 config=_config, style=_config['style'])

    ###################################################################################
    # Configure handlers
    ###################################################################################
    handlers = []
    # Configure stream handler if required.
    if _config['stream']:
        if not _config['monochrome']:
            s = RainbowStreamHandler(stream=_config['stream'],
                                     palette=_config['palette'])
        else:
            s = logging.StreamHandler(stream=_config['stream'])
        s.setFormatter(stream_formatter)
        handlers.append(s)

    # Configure file handler if required.
    if _config['filename']:
        f = logging.FileHandler(_config['filename'])
        f.setFormatter(file_formatter)
        handlers.append(f)

    ###################################################################################
    # Final config
    ###################################################################################
    for h in handlers:
        root.addHandler(h)

    # Set level
    root.setLevel(_config['level'])

    # Enhance the root log
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
