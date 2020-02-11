import logging
import sys
import functools
import inspect

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
        'remote_filename': (None, "green", False),
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