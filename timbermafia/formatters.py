import logging
import shutil
import sys
import timbermafia.utils as utils


def configure_timbermafia_formatter(style, palette):
    """Simple function to use a Style to create
    a timbermafia formatter instance."""
    return TimbermafiaFormatter(
        style.format,
        style.datefmt,
        style.format_style,
        timbermafia_style=style,
        palette=palette
    )


def configure_default_formatter(style):
    """Simple function to use a Style to create
    a basic logging.Formatter instance."""
    if sys.version_info[1] < 8:
        return logging.Formatter(
            style.simple_format,
            style.datefmt,
            style.format_style,
        )
    else:
        return logging.Formatter(
            style.simple_format,
            style.datefmt,
            style.format_style,
            validate=False
        )


class TimbermafiaFormatter(logging.Formatter):
    """Colourisation of output and vertically aligned columns.

    Logging.Formatter subclass enabling text-columns and
    multiline output, configured in a Timbermafia.Style class
    that is owned by the formatter.

    Is Liskov compliant with logging.Formatter.
    """

    def __init__(self, fmt=None, time_fmt=None, style='%',
                 validate=False,
                 timbermafia_style=None,
                 palette=None):
        """
        Usual init for logging.Formatter, and if a style is given, add
        it and set the number of columns.
        """

        # Validation was only included in python 3.8, so pass the
        # version-dependent args to the Formatter init.
        # print(sys.version_info)
        if sys.version_info[1] < 8:
            super().__init__(fmt, time_fmt, style)
        else:
            super().__init__(fmt, time_fmt, style, validate=validate)

        self.style = timbermafia_style
        self.palette = palette
        self.n_columns = None
        if self.style:
            self.style.generate_column_settings()
            self.n_columns = self.style.width_to_use

    def format_column_contents(self, record):
        """
        Creates a map of the column's template key to a list
        of lines to be output.
        """
        column_dict = self.style.generated_settings['columns']
        formatted_string_dict = {}

        # Iterate over columns and take the most efficient action based
        # on the length of the fully-formatted text.
        for key, c in column_dict.items():

            # Get the message components we care about first.
            # Also cast them to TMStrings
            record_dict = {
                k: v for k, v in record.__dict__.items()
                if k in c.fields
            }

            # If short_levels are enabled, abbreviate the level name.
            if self.style.short_levels:
                if 'levelname' in record_dict:
                    record_dict['levelname'] = record_dict['levelname'][0].upper()

            # Once all record modification is complete, cast everything to
            # TMStrings so they can use our format spec.
            record_dict = {k: utils.TMString(v) for k, v in record_dict.items()}

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
        template = self.style.generated_settings['template']

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
            sd = {
                key: s.return_separator_string(line_index)
                for key, s in
                self.style.generated_settings['separators'].items()
            }

            # Add separator dict to column dict and format
            cd.update(sd)
            full_lines.append(template.format(**cd))

        # If requested, colour the output by the log level.
        if self.style.colourised_levels:
            full_lines = self.get_colourised_output_by_level(full_lines,
                                                             record)

        # Join each with a newline and return.
        return '\n'.join(full_lines)

    def get_colourised_output_by_level(self, lines, record):
        """
        Takes a list of lines and applies ANSI formatting based on the
        Palette and log level.
        """
        levelno = record if isinstance(record, str) else record.levelno
        return self.palette.get_colourised_lines(levelno, lines)

    def format(self, record):
        """
        Format a LogRecord and return a string to be used by the
        linked Handler.
        """
        # If there is no timbermafia style, defer to Formatter.format
        if not self.style:
            return super().format(record)

        # If the terminal output has changed since the last call,
        # and fit_to_terminal is true, regenerate the columns.
        if self.style.fit_to_terminal:
            current_n_columns = shutil.get_terminal_size().columns
            if self.n_columns != current_n_columns:
                self.style.generate_column_settings()
                self.n_columns = current_n_columns

        # If requested, clean output.
        if self.style.clean_output:
            record.name = record.name.replace('root.', '')
            # record.funcName = record.funcName.replace('<module>', '')

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
