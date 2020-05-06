import logging
import sys
import timbermafia.formats
from timbermafia.palettes import PALETTE_DICT, Palette
from timbermafia.formatters import TimbermafiaFormatter
from timbermafia.styles import Style
import timbermafia.utils as utils


def configure_custom_formatter(style, palette):
    """Simple function to use a Style to create
    a timbermafia formatter instance."""
    return TimbermafiaFormatter(
        style.log_format,
        style.time_format,
        style.format_style,
        timbermafia_style=style,
        palette=palette
    )


def configure_default_formatter(style):
    """Simple function to use a Style to create
    a basic logging.Formatter instance."""
    return logging.Formatter(
        style.simple_log_format,
        style.time_format,
        style.format_style
    )


def generate_style_from_preset(preset):
    return Style(preset=preset)


def generate_palette_from_preset(preset):
    return Palette(preset=preset)

def basic_config(
        style=None, format=None, stream=None, filename=None,
        palette='sensible', silent=False,
        clear=False, basic_files=True, handlers=None, level=logging.DEBUG,
        ):
    """Function for basic configuration of timbermafia logging.

    Describe Args here
    """
    logging._acquireLock()
    try:

        # If we have no handlers, filename and no stream, assume we want a
        # stream piped to stdout
        if not stream and not filename and not handlers:
            stream = sys.stdout

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
                my_style = Style(preset=style, format=format)
            else:
                my_style = Style(preset=style)

        # If the given palette is a Palette instance, use it.
        # Else generate a palette from the preset.
        my_palette = palette
        if not isinstance(palette, Palette):
            my_palette = Palette(preset=palette)

        if use_custom_formatter:
            custom_formatter = configure_custom_formatter(my_style, my_palette)

        use_default_formatter = filename and not basic_files
        if use_default_formatter:
            # In line below we'll add the basic format from the style property
            default_formatter = configure_default_formatter(my_style)

        # Add stream handler if specified
        if stream:
            h = logging.StreamHandler(stream=sys.stdout)
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
