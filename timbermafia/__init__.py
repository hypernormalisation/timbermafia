"""Python package that makes implementing good-looking and flexible logging easy.

This package can provide one-line configurations of good-looking
and visually clear logging, based on the following core features:
    - an expanded fmt_spec for logging formats, allowing for individual
    log record fields to be displayed with any colour or appearance possible
    with ANSI codes.
    - colourisation of logging output indicating the output's log level.
    - a vertically aligned, column-based approach to displaying output
    to improve visual clarity in long messages, that adaptively assigns
    widths to individual columns.

A set of default styles and colour palettes are provided. A concise, colourful
logging appearance for stdout can be obtained by something as simple as:

    import timbermafia as tm
    tm.basic_config()

in a manner analogous to logging.basicConfig, but much more powerful.

Styles and colour palettes are fully customisable.

Adaptive widths are used to ensure columns receive the room they need
to display their text legibly. The user can also specify that certain
outputs be sensibly truncated to fit on a single line.

Supports resizing of output to match terminal widths as they change during
an application.
"""
__name__ = 'timbermafia'
__author__ = 'Stephen Ogilvy'

import logging
import sys
import threading

import timbermafia.formatters
import timbermafia.palettes
import timbermafia.styles
import timbermafia.utils


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


def generate_default_palette():
    """Returns an instance of the Palette class with the default settings."""
    return timbermafia.palettes.Palette(preset='sensible')


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
          ', '.join(timbermafia.palettes.palette_map))


############################################################
# Make basic_config thread safe, copied from logging.
############################################################
_lock = threading.RLock()


def _acquire_lock():
    """
    Acquire the module-level lock for serializing access to shared data.
    This should be released with _releaseLock().
    """
    if _lock:
        _lock.acquire()


def _release_lock():
    """
    Release the module-level lock acquired by calling _acquireLock().
    """
    if _lock:
        _lock.release()


############################################################
# Function to have timbermafia configure logging
# for an application.
############################################################
# noinspection PyShadowingBuiltins
def basic_config(
        name=None,
        stream=None,
        filename=None, filemode='a', basic_files=False,
        style=None, palette='sensible',
        format=None, datefmt=None, level=logging.DEBUG,
        silent=False, clear=False,
        handlers=None,
        width=None, fit_to_terminal=False,
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
    format and date format. timbermafia formats can support a fmt_spec and
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

    If a column escape is provided ("_" by default) then this splits output
     on either side into vertically aligned columns.
    The character or characters immediately following this escape until any
    whitespace are column separator characters that will be printed.
    If whitespace immediately follows the escape, no separator character is
    printed.
    A single escape means any characters are printed on the first line of
    multi-line printout, a double escape prints output on all lines of
    multi-line output.

    e.g. the following format
        {asctime} _| {name}.{funcName} __>> {message}
    will produce output like
        11:44:13 | MyLog.my_function >> I am an arbitrarily long message
                                     >> that is printed over several lines.

    Args:
        name: If given, configures a logger with that name that can be retrieved
            later with logging.getLogger. If not given, the logging library's
            root logger is modified, which should be used with caution! For
            instance, this will enable *all* logging for each library you use!
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
        fit_to_terminal: If enabled, tells the style to fit the output
            width to the terminal width. Useful in console or terminal emulator
            output, but doesn't behave well in Jupyter notebooks.
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
        width: the width in columns for the log output.
    """
    _acquire_lock()
    try:
        custom_formatter = get_timbermafia_formatter(
            style, palette, format, datefmt, width, fit_to_terminal
        )

        # If we have no handlers, no filename, and no stream then
        # assume we want a stream on stdout.
        if not stream and not filename and not handlers:
            stream = sys.stdout

        handlers = handlers if handlers else []
        # Add stream handler if specified
        if stream:
            h = logging.StreamHandler(stream=stream)
            h.setFormatter(custom_formatter)
            handlers.append(h)
        # Add file handler if specified
        if filename:
            h = logging.FileHandler(filename, filemode)
            if basic_files:
                f = timbermafia.formatters.configure_default_formatter
                default_formatter = f(custom_formatter.style)
                h.setFormatter(default_formatter)
            else:
                h.setFormatter(custom_formatter)
            handlers.append(h)

        # Now configure the logger objects as needed.
        # If working with the root logger, only one logger is required.
        # If we're working with a named logger, we need to clone this logger
        # to be picked up by classes inheriting from timbermafia.Logged.
        loggers = []
        if name:
            loggers.append(logging.getLogger(name))
            loggers.append(logging.getLogger('timbermafia_mixin'))
        else:
            loggers.append(logging.root)
        for logger in loggers:
            if clear:
                for h in logger.handlers[:]:
                    logger.removeHandler(h)
                    h.close()
            for h in handlers:
                logger.addHandler(h)
            logger.setLevel(level)

        if not silent:
            print('- timbermafia has configured handlers:')
            for h in handlers:
                print('  -', h)
            if name:
                print(f'- name {name} given, generated named logger.')
            else:
                print('- no name given, manipulated the root logger. Warning:'
                      ' this will alter *all* logging in your application, '
                      'including in the libraries you use!')
    finally:
        _release_lock()


# noinspection PyShadowingBuiltins
def get_timbermafia_formatter(
        style=None, palette='sensible',
        format=None, datefmt=None,
        width=None, fit_to_terminal=False,
        ):
    """
    Return an instance of the TimbermafiaFormatter according to the given
    specification. This can be used in more complex configurations of
    handlers and loggers than basic_config can provide.

    Args:
        style: The name of the timbermafia style to use. Available styles can
            be viewed with timbermafia.print_styles(). Note that this is not
            analogous to the style arg that logging Formatters accept, and
            timbermafia only supports the '{', or StrFormat, style.
        fit_to_terminal: If enabled, tells the style to fit the output
            width to the terminal width. Useful in console or terminal emulator
            output, but doesn't behave well in Jupyter notebooks.
        palette: The name of the timbermafia colour palette to use. Available
            palettes can be viewed with timbermafia.print_palettes().
        format: Use the specified format string in the Formatter. timbermafia
            formats can use an expanded format spec, and vertically aligned
            columns can be declared with the appropriate escape character, by
            default '_'.
        datefmt: Use the specified date/time format in the Formatter.
        width: the width in columns for the log output.

    Returns:
        A TimbermafiaFormatter instance configured to spec.
    """
    my_style = style
    if not isinstance(style, timbermafia.styles.Style):
        my_style = generate_style_from_preset(style)
    if format:
        my_style.format = format
    if datefmt:
        my_style.datefmt = datefmt
    if width:
        my_style.width = int(width)
    my_style.fit_to_terminal = fit_to_terminal

    my_palette = palette
    if not isinstance(palette, timbermafia.palettes.Palette):
        my_palette = generate_palette_from_preset(palette)

    f = timbermafia.formatters.configure_timbermafia_formatter
    return f(my_style, my_palette)


############################################################
# A class providing a mix-in logger
############################################################
class Logged:
    """Provides a mix-in logger for subclasses.

    The log name ensures the root logger is in the logger
    hierarchy, and that its handlers can be used.

    Timbermafia can clean up the "timbermafia_mixin." from the output
    automatically for visual clarity.
    """
    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'timbermafia_mixin.{self.__class__.__name__}')


############################################################
# Functions to support titles in loggers.
############################################################
def get_width_from_log(log):
    """A function to get the log width from the style object,
    if we can find a TimbermafiaFormatter attached to any handler."""
    for h in log.handlers:
        if isinstance(h.formatter,
                      timbermafia.formatters.TimbermafiaFormatter):
            if hasattr(h.formatter, "style"):
                return h.formatter.style.width_to_use


def header(self, msg):
    """Function to be monkey-patched onto the
    logging.Logger class if requested."""
    self.info(timbermafia.utils.divider_uuid)
    self.info('_'.join([timbermafia.utils.title_uuid,
                       msg]))
    self.info(timbermafia.utils.divider_uuid)


def monkey_patch_logger():
    """If run, will monkey patch the header function onto the
    logging.Logger class to allow all Logger objects in the application
    to use header."""
    logging.Logger.header = header
