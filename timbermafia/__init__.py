import inspect
import logging
import sys
import textwrap
import functools
from logging import root
from timbermafia.rainbow import RainbowStreamHandler

_valid_styles = ['default', 'test1']

LONGEST_LEVEL_NAME = len(max(list(logging._nameToLevel.keys())))

total_columns = 120
caller_padding = 25
time_padding = 14
total_padding = caller_padding + time_padding
printable_area = total_columns - total_padding


divider_flag = 'divider_replace_me'


def divider():
    return divider_flag


def enhance(log):
    levels = []
    for level_name in logging._nameToLevel.keys():
        if level_name != 'NOTSET':
            levels.append(level_name.lower())
    levels = set(levels)
    funcs = [getattr(root, level) for level in levels]
    for func, level in zip(funcs, levels):
        setattr(log, f'h{level}', headed_log(func=func))


def configure_root_logger(*args, **kwargs):
    """Function to configure the root logger in logging, analagous to logging.basicConfig"""
    # Reset handlers
    force = kwargs.get('force', True)
    if force:
        for h in root.handlers[:]:
            root.removeHandler(h)
            h.close()

    # Pre-determined style
    style = kwargs.get('style', 'default')
    if style not in _valid_styles:
        raise ValueError(f'"style" must be one of: {", ".join(_valid_styles)}')

    ###################################################################################
    # Configure formatters
    ###################################################################################
    show_level = kwargs.get('show_level', False)
    user_format = kwargs.get('format', False)
    time_format = kwargs.get('time_format', '%H:%M:%S')
    format_style = kwargs.get('format_style', '{')

    my_format = user_format if user_format else '{asctime} | {name}.{funcName} | {message}'
    my_format_loglevel = user_format if user_format else '{asctime} | {levelname} | {name}.{funcName} | {message}'
    format_to_use = my_format_loglevel if show_level else my_format

    stream_formatter = TMFormatter(format_to_use, time_format,
                                               style=format_style)
    file_formatter = TMFormatter(my_format_loglevel, time_format,
                                             style=format_style)

    ###################################################################################
    # Configure handlers
    ###################################################################################
    handlers = []
    # Configure stream handler if required.
    stream = kwargs.get('stream', None)
    show_colour = kwargs.get('show_colour', True)
    if stream:
        if show_colour:
            s = RainbowStreamHandler(stream=stream)
        else:
            s = logging.StreamHandler(stream=stream)
        s.setFormatter(stream_formatter)
        handlers.append(s)

    # Configure file handler if required.
    filename = kwargs.get('filename', None)
    if filename:
        f = logging.FileHandler(filename)
        f.setFormatter(file_formatter)
        handlers.append(f)

    ###################################################################################
    # Final config
    ###################################################################################
    for h in handlers:
        root.addHandler(h)

    # Set level
    level = kwargs.get('level', 'DEBUG')
    root.setLevel(level)

    # Enhance the root log
    enhance(logging.Logger)


###########################################################################
# Custom logging classes.
###########################################################################
# class RainbowStreamHandler(logging.StreamHandler):
#     # color names to indices
#     color_map = {
#         "black": 0,
#         "red": 1,
#         "green": 2,
#         "yellow": 3,
#         "blue": 4,
#         "magenta": 5,
#         "cyan": 6,
#         "white": 7 if use_alt_colors else 0,
#     }
#
#     # level colour specifications
#     # syntax: logging.level: (background color, foreground color, bold)
#     level_map = {
#         'local_filename': (None, "cyan", False),
#         'remote_filename': (None, "green", False),
#         logging.DEBUG: (None, "blue", False),
#         logging.INFO: (None, "white", False),
#         logging.WARNING: (None, "yellow", False),
#         logging.ERROR: (None, "red", False),
#         logging.CRITICAL: ("red", "white", False),
#     }
#
#     # control sequence introducer
#     CSI = "\x1b["
#
#     # normal colours
#     reset = "\33["
#
#     def istty(self):
#         isatty = getattr(self.stream, "isatty", None)
#         return isatty and isatty()
#
#     def emit(self, record):
#         try:
#             message = self.format(record)
#             stream = self.stream
#             if not self.istty:
#                 stream.write(message)
#             else:
#                 self.output_colorized(message)
#             stream.write(getattr(self, "terminator", "\n"))
#             self.flush()
#         except (KeyboardInterrupt, SystemExit):
#             raise
#         except:
#             self.handleError(record)
#
#     def output_colorized(self, message):
#         self.stream.write(message)
#
#     def colorize(self, message, record):
#         levelno = None
#         # print(record, isinstance(record, str))
#         if isinstance(record, str):
#             levelno = record
#         else:
#             levelno = record.levelno
#         if levelno in self.level_map:
#             background_color, foreground_color, bold = self.level_map[levelno]
#             parameters = []
#             if background_color in self.color_map:
#                 parameters.append(str(self.color_map[background_color] + 40))
#             if foreground_color in self.color_map:
#                 parameters.append(str(self.color_map[foreground_color] + 30))
#             if bold:
#                 parameters.append("1")
#             if parameters:
#                 message = "".join(
#                     (self.CSI, ";".join(parameters), "m", message, self.reset)
#                 )
#         return message
#
#     def format(self, record):
#         message = logging.StreamHandler.format(self, record)
#         # print('tc:', record)
#         if self.istty:
#             # Colorise all multiline output.
#             parts = message.split("\n", 1)
#             for index, part in enumerate(parts):
#                 parts[index] = self.colorize(part, record)
#             message = "\n".join(parts)
#             # Now colorise all file names.
#             parts = message.split(' ')
#             # print(parts)
#             for index, part in enumerate(parts):
#                 if not part:
#                     continue
#                 if part[0] == '/':
#                     parts[index] = self.colorize(part, 'local_filename')
#                 elif part.startswith('http') or part.startswith('www'):
#                     parts[index] = self.colorize(part, 'remote_filename')
#             message = " ".join(parts)
#         return message


# def log(function):
#     @functools.wraps(function)
#     def decoration(
#             *args,
#             **kwargs
#     ):
#         # Get the names of all of the function arguments.
#         arguments = inspect.getcallargs(function, *args, **kwargs)
#         logging.debug(
#             "function '{function_name}' called by '{caller_name}' with arguments:"
#             "\n{arguments}".format(
#                 function_name=function.__name__,
#                 caller_name=inspect.stack()[1][3],
#                 arguments=arguments
#             ))
#         result = function(*args, **kwargs)
#         logging.debug("function '{function_name}' result: {result}\n".format(
#             function_name=function.__name__,
#             result=result
#         ))
#     return decoration


class TMFormatter(logging.Formatter):
    """Formatter for our logging, pretty as a picture, natural splendour etc."""

    @staticmethod
    def set_caller_name(my_name):
        """
        A function to take the caller string (the bit in the log printout
        which tells you where the call was made) and format it, to make sure
        it fits the rest of the printout.
        """
        # First of all, if we are running a header, return an empty string.
        if 'decorator_divider' in my_name:
            return ''
        # If any unhelpful terms appear chuck them.
        terms_to_remove = ['.<module>']  # , '.__init__']

        # Remove any leading ' root.' for class logs
        if my_name.startswith(' root.'):
            my_name = my_name[6:]

        for term in terms_to_remove:
            if term in my_name:
                my_name = my_name.replace(term, '')

        # If there is enough room for the full caller designation, return it.
        if len(my_name) <= caller_padding:
            return my_name
        return '...' + my_name[-caller_padding + 2:]

    def format(self, record):

        show_level_name = 'levelname' in self._fmt

        s = super(TMFormatter, self).format(record)

        if divider_flag in s:
            s = total_columns * '-'
            return s

        if '\nTraceback (most recent call last)' in s:
            print(s)

        split_list = s.split('|')
        # Find exceptions and remove them from the string, for separate handling.
        # if '\nTraceback (most recent call last)' in split_list[-1]:
        #     s = split_list[-1]
        #     i = s.find('\nTraceback (most recent call last)')
        #     split_list[-1] = s[:i]
        #     exception_message = s[i:]
        #     print(RED + exception_message + '\n')

        # Get the timestamp.
        timestamp = split_list[0]
        caller_name = self.set_caller_name(split_list[1])
        print_statement = split_list[2]

        # Make a list of print_statements that need to be prepended
        # with the time and caller info.
        # Take off some characters because textwrap.wrap soft wraps.
        s_list = textwrap.wrap(print_statement, printable_area - 3,
                               break_long_words=True)

        # Now we need to construct each individual printout string from the time,
        # caller, and print info.
        for index, printout in enumerate(s_list):
            # If it's the first line, add the timestamp and caller.
            if index == 0:
                # pad the caller name to be the required length
                caller_name = caller_name.rjust(caller_padding + 1)
                the_string = timestamp + '| ' + caller_name + '|' + printout
            else:
                the_string = (len(timestamp) * ' ' + '| ' +
                              ''.rjust(caller_padding + 1) + '| ' + printout)
            s_list[index] = the_string

        s = '\n'.join(s_list).strip(" ")
        return s


def headed_log(func):
    """A decorator for header breaks in stdout."""

    def decorator_divider(self, *args, **kwargs):
        func(divider())
        func(*args, **kwargs)
        func(divider())

    return decorator_divider
#


class Logged:
    """
    Inherit from this class to provide a mixin logger via
    the log property.
    """

    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'root.{self.__class__.__name__}')

# log = logging.getLogger(__name__)
# sh = ColorisingStreamHandler(sys.stdout)
# f = TMFormatter(
#     '{asctime} | {name}.{funcName} | {message}',
#     '%H:%M:%S', style='{'
# )
# sh.setFormatter(f)
# log.setLevel(logging.DEBUG)
# log.addHandler(sh)
# log.headed_info = headed_log(log.info)
# log.headed_debug = headed_log(log.debug)

# def enhance(log):


# print(__name__)
#
# def test_func_log():
#     log.info('I am called from within the function test_func_log')
#
#
# def test_func_log2():
#     log.info('I am called from within the function test_func_log2')
