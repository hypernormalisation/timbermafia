import logging
import sys
import timbermafia.formatters
import timbermafia.palettes
import timbermafia.styles
import timbermafia.utils as utils


############################################################
# Functions to generate style/palette objects from presets.
############################################################
def generate_default_style():
    """Returns an instance of the Style class with the default settings."""
    return timbermafia.styles.Style(preset='default')


def generate_style_from_preset(preset):
    """Generate a Style object from a preset style.

    Args:
        preset: A string with the name of a preset style.

    Returns:
        Instance of the Style class with settings according to the
        specified preset.
    """
    return timbermafia.styles.Style(preset=preset)


def generate_palette_from_preset(preset):
    """Generate a Palette object from a preset palette.

    Args:
        preset: A string with the name of a preset palette.

    Returns:
        Instance of the Palette class with settings according to the
        specified preset.
    """
    return timbermafia.palettes.Palette(preset=preset)


############################################################
# Functions to show info on available styles/palettes.
############################################################
def print_styles():
    """Print preset styles with their descriptions."""
    print('- Preset styles:')
    for style, conf in timbermafia.styles.style_map.items():
        print(f'{style} -'.rjust(16), conf['description'])


def print_palettes():
    """Print the preset colour palettes."""
    print('- Preset palettes:', ', '.join(timbermafia.palettes.palette_dict))


############################################################
# Function to have timbermafia configure logging
# for an application.
# Analogous to logging.basicConfig
############################################################
def basic_config(
        stream=None, filename=None, filemode='a',
        style=None, palette='sensible',
        format=None, datefmt=None,
        silent=False, clear=False, basic_files=True,
        handlers=None, level=logging.DEBUG,
        ):
    """Function for basic configuration of timbermafia logging.

    Describe Args here
    """
    logging._acquireLock()
    try:

        # Reference to the root logger
        logger = logging.root

        # If we have no handlers, filename and no stream, assume we want a
        # stream piped to stdout.
        if not stream and not filename and not handlers:
            stream = sys.stdout

        # If no handlers set an empty list.
        handlers = handlers if handlers else []

        # Reset existing handlers if needed
        if clear:
            for h in logger.handlers[:]:
                logger.removeHandler(h)
                h.close()

        # If the given style is a Style instance, use it.
        # Else generate a style from the preset, and
        # set the format and datefmt if specified.
        my_style = style
        if not isinstance(style, timbermafia.styles.Style):
            my_style = generate_style_from_preset(style)
        if format:
            my_style.format = format
        if datefmt:
            my_style.datefmt = datefmt

        # If the given palette is a Palette instance, use it.
        # Else generate a palette from the preset.
        my_palette = palette
        if not isinstance(palette, timbermafia.palettes.Palette):
            my_palette = generate_palette_from_preset(palette)

        # Only create formatters and styles as required.
        use_custom_formatter = stream or (filename and not basic_files)
        custom_formatter, default_formatter = None, None
        if use_custom_formatter:
            f = timbermafia.formatters.configure_custom_formatter
            custom_formatter = f(my_style, my_palette)
        use_default_formatter = filename and basic_files
        if use_default_formatter:
            f = timbermafia.formatters.configure_default_formatter
            default_formatter = f(my_style)

        # Add stream handler if specified
        if stream:
            h = logging.StreamHandler(stream=stream)
            h.setFormatter(custom_formatter)
            handlers.append(h)

        # Add file handler if specified
        if filename:
            h = logging.FileHandler(filename, filemode)
            if basic_files:
                h.setFormatter(default_formatter)
            else:
                h.setFormatter(custom_formatter)
            handlers.append(h)

        # Set logging levels for handlers and root logger.
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


############################################################
# A class that if inherited from will provide a mixin logger
############################################################
class Logged:
    """
    Inherit from this class to provide a mixin logger via
    the log property.

    The log name ensures the root logger is in the logger
    hierarchy, and that its handlers can be used.

    Timbermafia can clean up the "root." from the output
    automatically for visual clarity.
    """
    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'root.{self.__class__.__name__}')
