# import ansiwrap
import logging
import re
import shutil
import string
import sys
import textwrap
from timbermafia.utils import *
import timbermafia.utils as utils


class TimbermafiaFormatter(logging.Formatter):

    def __init__(self, fmt=None, time_fmt=None, style='%',
                 validate=False, timbermafia_style=None):

        super().__init__(fmt, time_fmt, style, validate=validate)
        self.style = timbermafia_style
        self.conf, self.n_columns = None, None

        if self.style:
            self.conf = self.style.generate_column_settings()
            self.n_columns = self.style.conf.get(
                'n_columns', shutil.get_terminal_size().columns
            )

    def format_column_contents(self, record):
        """Creates a map of the column's template key to a list
        of lines to be output"""
        column_dict = self.conf['columns']

        formatted_string_dict = {}

        for key, c in column_dict.items():

            # Get the message components we care about first.
            # Also cast them to TMStrings
            record_dict = {
                k: utils.TMString(v) for k, v in record.__dict__.items()
                if k in c.fields
            }

            # Use the basic format to see if we need truncation.
            # print(c.fmt)
            # print(c.fmt_basic)
            s = c.fmt_basic.format(**record_dict)
            # print(c.fmt_basic, c.reserved_padding)
            # print(s, len(s))

            # For fixed length columns, or incidental
            # cases where the string "just fits", a simple
            # format to the full format works.

            # print(s, c.reserved_padding)
            # print(c.__dict__)
            # print(c.truncate_enabled)

            if len(s) == c.reserved_padding:
                s = c.fmt.format(**record_dict)
                # print(s)
                formatted_string_dict[key] = [s]

            # If the string is longer we need to either truncate the output
            # if that setting is enabled, or delegate the to multiline func.

            elif len(s) > c.reserved_padding:
                # print(c.__dict__)

                # print(f'{c} needs truncating')
                if c.truncate_enabled:
                    # print('TRUNCATING:')
                    # print(c.__dict__)
                    s = c.truncate_input(record_dict)
                    formatted_string_dict[key] = [s]
                else:
                    lines = c.format_multiline(record_dict)
                    s = 'SOMETHING WILL GO HERE'
                # new_fmt = d['new_format']
                # new_record_dict = d['new_record_dict']
                #
                # s_full = new_fmt.format(**new_record_dict)
                # print(s)
                    formatted_string_dict[key] = lines

            # Else the string is shorter than the padding, and
            # we need justification and padding
            else:
                s = c.justify_and_pad_input(record_dict)
                formatted_string_dict[key] = [s]

        # If there is multiline, pad any unused space for columns
        # with contents running less than the n_lines
        # print(formatted_string_dict)

        max_lines = max([len(l) for l in formatted_string_dict.values()])
        # print(max_lines)

        for key, lines in formatted_string_dict.items():

            while len(lines) < max_lines:
                lines.append(column_dict[key].empty_padding_string)
            # print(key, lines)
            formatted_string_dict[key] = lines

        return formatted_string_dict

    def form_output_string(self, column_string_dict):

        full_lines = []
        template = self.conf['template']
        n_lines = 0
        for lines in column_string_dict.values():
            n_lines = len(lines)
            break
        # print('n_lines says', n_lines)

        for line_index in range(n_lines):
            cd = {key: lines[line_index] for
                  key, lines in column_string_dict.items()}
            # print(cd)

            sd = {key: s.return_separator_string(line_index)
                for key, s in self.conf['separators'].items()
            }
            # print(sd)

            # Add separator dict to column dict and format
            cd.update(sd)

            full_lines.append(template.format(**cd))

        # print(full_lines)
        return '\n'.join(full_lines)
        # # Take care of separators.
        # separator_dict = self.conf['separators']
        # # print(separator_dict)
        # sd2 = {key: s.content_escaped for key, s in separator_dict.items()}
        # # print(sd2)
        # sd2.update(formatted_string_dict)
        # template = self.conf['template']
        # # print(template)
        # return template.format(**sd2)

    # def convert_log_record_properties(self, record):
    #     """Convert the log record's component strings to TMStrings."""
    #     record.message = TMString(record.getMessage())
    #     if self.usesTime():
    #         record.asctime = TMString(self.formatTime(record, self.datefmt))
    #     new_d = {}
    #     for key, value in record.__dict__.items():
    #         if key in self.style.fields and isinstance(value, str):
    #             # print(f'converting {key}: {value}')
    #             new_d[key] = TMString(value)
    #     record.__dict__.update(new_d)

    def format(self, record):

        # If there is no timbermafia style, defer to Formatter.format
        if not self.style:
            return super().format(record)

        # If requested, clean output.
        if self.style.clean_output:
            record.name = record.name.replace('__module__', '')
            record.name = record.name.replace('root.', '')

        # Convert the message string to an TMString with enhanced fmt_spec
        record.message = record.getMessage()
        #
        # # Convert the formatted ascitime string to an TMString with enhanced fmt_spec
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        d = self.format_column_contents(record)
        s = self.form_output_string(d)

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
        # print(s)
        return s
