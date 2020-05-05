import logging
import re
import shutil
import timbermafia.utils as utils


class TimbermafiaFormatter(logging.Formatter):
    """
    Logging.Formatter subclass enabling text-columns and
    multiline output, configured in a Timbermafia.Style class
    that is owned by the formatter.

    Is Liskov compliant with logging.Formatter.
    """

    def __init__(self, fmt=None, time_fmt=None, style='%',
                 validate=False, timbermafia_style=None):
        """
        Usual init for logging.Formatter, and if a style is given, add
        it and set the number of columns.
        """
        super().__init__(fmt, time_fmt, style, validate=validate)
        self.style = timbermafia_style
        self.conf, self.n_columns = None, None

        if self.style:
            self.conf = self.style.generate_column_settings()
            self.n_columns = self.style.conf.get(
                'n_columns', shutil.get_terminal_size().columns
            )

    def format_column_contents(self, record):
        """
        Creates a map of the column's template key to a list
        of lines to be output.
        """
        column_dict = self.conf['columns']
        formatted_string_dict = {}

        # Iterate over columns and take the most efficient action based
        # on the length of the fully-formatted text.
        for key, c in column_dict.items():

            # Get the message components we care about first.
            # Also cast them to TMStrings
            record_dict = {
                k: utils.TMString(v) for k, v in record.__dict__.items()
                if k in c.fields
            }

            # Use the basic format to establish the length and establish
            # the most efficient approach.
            s = c.fmt_basic.format(**record_dict)

            # For fixed length columns, or incidental
            # cases where the string "just fits", a simple
            # format gives the correct padding.
            if len(s) == c.reserved_padding:
                s = c.fmt.format(**record_dict)
                formatted_string_dict[key] = [s]

            # If the string is longer we need to either truncate the output
            # if that setting is enabled, or delegate the to multiline func.
            elif len(s) > c.reserved_padding:
                if c.truncate_enabled:
                    s = c.truncate_input(record_dict)
                    formatted_string_dict[key] = [s]
                else:
                    lines = c.format_multiline(record_dict)
                    formatted_string_dict[key] = lines

            # Else the string is shorter than the padding, and
            # we need justification and padding.
            else:
                s = c.justify_and_pad_input(record_dict)
                formatted_string_dict[key] = [s]

        # If there is multiline, pad any unused space for columns
        # with contents running less than the n_lines
        max_lines = max([len(lines) for lines in
                         formatted_string_dict.values()])
        if max_lines > 1:
            for key, lines in formatted_string_dict.items():
                while len(lines) < max_lines:
                    lines.append(column_dict[key].empty_padding_string)
                formatted_string_dict[key] = lines

        return formatted_string_dict

    def form_output_string(self, column_string_dict, record):
        """
        Take the map of the template key mapped to the lines,
        combine with the separators, and return the full string
        to be pushed to the Handlers.
        """
        full_lines = []
        template = self.conf['template']

        # Get the number of lines (the lengths of the lines are
        # the same for all columns at this stage).
        n_lines = 0
        for lines in column_string_dict.values():
            n_lines = len(lines)
            break

        # Iterate over each line and construct the string for that line.
        for line_index in range(n_lines):
            cd = {key: lines[line_index] for
                  key, lines in column_string_dict.items()}

            # Get the separators for this line index.
            sd = {key: s.return_separator_string(line_index)
                for key, s in self.conf['separators'].items()
            }

            # Add separator dict to column dict and format
            cd.update(sd)
            full_lines.append(template.format(**cd))

        # If requested, colour the output by the log level.
        if not self.style.monochrome:
            full_lines = self.get_colour_output_by_level(full_lines, record)

        # Join each with a newline and return.
        return '\n'.join(full_lines)

    def get_colour_output_by_level(self, lines, record):
        """
        Takes a list of lines and applies ANSI formatting based on the
        Style's colour palette.
        """
        # Get the palette settings.
        level = record if isinstance(record, str) else record.levelno
        palette_settings = self.style.palette.get(level)
        if not palette_settings:
            return lines

        fg_colour, bg_colour, bold = palette_settings
        total_ansi = ''
        if fg_colour:
            total_ansi += utils.fg.format(fg_colour)
        if bg_colour:
            total_ansi += utils.bg.format(bg_colour)
        if bold:
            total_ansi += utils.BOLD

        new_lines = []
        for line in lines:
            # Add the colour at the start of the line
            line = total_ansi + line
            # Now find any resets and replace them with a
            # reset + our new ansi.
            line = line.replace(utils.RESET, utils.RESET+total_ansi)
            # Add a final reset
            line = line + utils.RESET
            new_lines.append(line)

        return new_lines

    def format(self, record):
        """
        Format a LogRecord and return a string to be used by the
        linked Handler.
        """
        # If there is no timbermafia style, defer to Formatter.format
        if not self.style:
            return super().format(record)

        # If requested, clean output.
        if self.style.clean_output:
            # print(record.funcName)
            # record.funcName = record.funcName.replace('.<module>', '')
            record.name = record.name.replace('root.', '')

        # Get the message and if necessary the time.
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        # Create a map of the template key to the column lines.
        d = self.format_column_contents(record)
        # Use that map and record to construct the full string.
        s = self.form_output_string(d, record)

        # Handle exceptions.
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)

        return s
