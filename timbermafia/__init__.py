import inspect
import logging
import sys
import textwrap
import functools

DARK_RED = "\033[0;31m"
RED = "\033[1;31m"
YELLOW = "\033[1;33m"
WHITE = "\033[1;37m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"
total_columns = 120
caller_padding = 40
time_padding = 14
total_padding = caller_padding + time_padding
printable_area = total_columns - total_padding

divider_flag = 'divider_replace_me'


def divider():
    return divider_flag


def run_from_ipython():
    try:
        # noinspection PyUnresolvedReferences
        __IPYTHON__
        return True
    except NameError:
        return False


# I'm so sorry this is because of Steve Jobs forgive me.
use_alt_colors = run_from_ipython()


class ColorisingStreamHandler(logging.StreamHandler):
    # color names to indices
    color_map = {
        "black": 0,
        "red": 1,
        "green": 2,
        "yellow": 3,
        "blue": 4,
        "magenta": 5,
        "cyan": 6,
        "white": 7 # if use_alt_colors else 0,
    }

    # level colour specifications
    # syntax: logging.level: (background color, foreground color, bold)
    level_map = {
        'local_filename': (None, "cyan", False),
        'remote_filename': (None, "red", False),
        logging.DEBUG: (None, "blue", False),
        logging.INFO: (None, "white", False),
        logging.WARNING: (None, "yellow", False),
        logging.ERROR: (None, "red", False),
        logging.CRITICAL: ("red", "white", True),
    }

    # control sequence introducer
    CSI = "\x1b["

    # normal colours
    reset = "\x1b[0m"

    def istty(self):
        isatty = getattr(self.stream, "isatty", None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.istty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, "terminator", "\n"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def output_colorized(self, message):
        self.stream.write(message)

    def colorize(self, message, record):
        levelno = None
        # print(record, isinstance(record, str))
        if isinstance(record, str):
            levelno = record
        else:
            levelno = record.levelno
        if levelno in self.level_map:
            background_color, foreground_color, bold = self.level_map[levelno]
            parameters = []
            if background_color in self.color_map:
                parameters.append(str(self.color_map[background_color] + 40))
            if foreground_color in self.color_map:
                parameters.append(str(self.color_map[foreground_color] + 30))
            if bold:
                parameters.append("1")
            if parameters:
                message = "".join(
                    (self.CSI, ";".join(parameters), "m", message, self.reset)
                )
        return message

    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        # print('tc:', record)
        if self.istty:
            # Colorise all multiline output.
            parts = message.split("\n", 1)
            for index, part in enumerate(parts):
                parts[index] = self.colorize(part, record)
            message = "\n".join(parts)
            # Now colorise all file names.
            parts = message.split(' ')
            # print(parts)
            for index, part in enumerate(parts):
                if not part:
                    continue
                if part[0] == '/':
                    parts[index] = self.colorize(part, 'local_filename')
                elif part.startswith('https'):
                    parts[index] = self.colorize(part, 'remote_filename')
            message = " ".join(parts)
        return message


def log(function):
    @functools.wraps(function)
    def decoration(
            *args,
            **kwargs
    ):
        # Get the names of all of the function arguments.
        arguments = inspect.getcallargs(function, *args, **kwargs)
        logging.debug(
            "function '{function_name}' called by '{caller_name}' with arguments:"
            "\n{arguments}".format(
                function_name=function.__name__,
                caller_name=inspect.stack()[1][3],
                arguments=arguments
            ))
        result = function(*args, **kwargs)
        logging.debug("function '{function_name}' result: {result}\n".format(
            function_name=function.__name__,
            result=result
        ))
    return decoration


class TMFormatter(logging.Formatter):
    """Formatter for our logging, pretty as a picture, natural splendour etc."""

    @staticmethod
    def set_caller_name(name):
        """
        A function to take the caller string (the bit in the log printout
        which tells you where the call was made) and format it, to make sure
        it fits the rest of the printout.
        """
        # First of all, if we are running a header, return an empty string.
        if 'decorator_divider' in name:
            return ''
        # If any unhelpful terms appear chuck them.
        terms_to_remove = []  # '.<module>', '.__init__']
        for term in terms_to_remove:
            if term in name:
                name = name.replace(term, '')
        # If there is enough room for the full caller designation, return it.
        if len(name) <= caller_padding:
            return name
        return '...' + name[-caller_padding + 2:]

    def format(self, record):
        s = super(TMFormatter, self).format(record)

        if divider_flag in s:
            s = total_columns * '-'
            return s

        split_list = s.split('|')
        # Find exceptions and remove them from the string, for separate handling.
        if '\nTraceback (most recent call last)' in split_list[-1]:
            s = split_list[-1]
            i = s.find('\nTraceback (most recent call last)')
            split_list[-1] = s[:i]
            exception_message = s[i:]
            print(RED + exception_message + '\n')

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

    def decorator_divider(*args, **kwargs):
        func(divider())
        func(*args, **kwargs)
        func(divider())

    return decorator_divider


class Logged:
    """
    A class to inherit from, such that the logger knows the
    name of the class making the call.
    """

    @property
    def log(self):
        """Property to return a mixin logger."""
        return logging.getLogger(f'timbermafia.{self.__class__.__name__}')


def ts_func_log(func):
    """
    Decorator for functions which override the log in the module
    namespace to use the correct name.
    """

    def wrapper(*args, **kwargs):
        log = logging.getLogger(f'timbermafia.{sys.modules[func.__module__].__name__}')
        r = func(*args, **kwargs)
        return r

    return wrapper

log = logging.getLogger(__name__)
sh = ColorisingStreamHandler(sys.stdout)
f = TMFormatter(
    '{asctime} | {name}.{funcName} | {message}',
    '%H:%M:%S', style='{'
)
sh.setFormatter(f)
log.setLevel(logging.DEBUG)
log.addHandler(sh)
log.headed_info = headed_log(log.info)
log.headed_debug = headed_log(log.debug)
print(__name__)

def test_func_log():
    log.info('I am called from within the function test_func_log')


def test_func_log2():
    log.info('I am called from within the function test_func_log2')
