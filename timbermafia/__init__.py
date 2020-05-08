import logging
import sys
import timbermafia.formatters
import timbermafia.palettes
import timbermafia.styles


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
    print('- Preset palettes:',
          ', '.join(timbermafia.palettes.palette_dict))


############################################################
# Function to have timbermafia configure logging
# for an application.
############################################################
def basic_config(
        stream=None, filename=None, filemode='a', basic_files=True,
        style=None, palette='sensible',
        format=None, datefmt=None, level=logging.DEBUG,
        silent=False, clear=False,
        handlers=None
        ):
    """Function for basic configuration of timbermafia logging.

    Configures python's logging with timbermafia's expanded formatting support.
    This function is analogous to logging.basicConfig. If called with no
    arguments it will configure a StreamHandler piped to stdout with a
    timbermafia formatter, with the default style and colour palette.

    Passing a stream or filename will configure a StreamHandler or FileHandler
    accordingly. The user can also supply their own logging handlers to be
    configured with a timbermafia formatter.

    The timbermafia style and palette can be specified, as can the logging
    format and date format.

    Pass clear=True to delete all existing logging handlers.

    Args:
        stream: Specifies that a StreamHandler be created using the given
            stream. If no stream or filename args given, a StreamHandler using
            stdout will be configured.
        filename: Specifies that a FileHandler be created using the given
            filename. Unlike in logging.basicConfig, can be passed with
            a stream.
        filemode: Specifies the mode in which to open the file, defaulting
            to 'a', appending output.
        basic_files: If true, and both a filename and stream are given, a
            simple version of the format without column or any fmt_spec
            is given to the FileHandler. This lack of ANSI codes or any
            whitespace can make log files smaller.
        style: The name of the timbermafia style to use. Available styles can
            be viewed with timbermafia.print_styles(). Note that this is not
            analogous to the style arg that logging Formatters accept, and
            timbermafia only supports the '{', or StrFormat, style.
        palette: The name of the timbermafia colour palette to use. Available
            palettes can be viewed with timbermafia.print_palettes().
        format: Use the specified format string in the Formatter. timbermafia
            formats can use an expanded format spec, and vertically aligned
            columns can be declared with the appropriate escape character, by
            default '_'.
        datefmt: Use the specified date/time format in the Formatter.
        level: Set the root logger and any given handlers to this level. Should
            be an int, easily accessible with e.g. logging.INFO.
        silent: Set to True to suppress this function printing information
            on the configuration to streams.
        clear: Set to True to remove any existing handlers attached to the
            root logger before carrying out any further configuration.
        handlers: Should be an iterable of handlers, which will be
            equipped with a timbermafia formatter and added to the root logger.
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
# A class providing a mix-in logger
############################################################
class Logged:
    """Provides a mix-in logger for subclasses.

    The log name ensures the root logger is in the logger
    hierarchy, and that its handlers can be used.

    Timbermafia can clean up the "root." from the output
    automatically for visual clarity.
    """
    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'root.{self.__class__.__name__}')
