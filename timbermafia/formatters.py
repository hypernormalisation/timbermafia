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
        # print(self.n_columns)

    # def _format(self, record):
    #     return self._fmt.format(**record.__dict__)

    # ct = self.converter(record.created)

    def get_formatted_columns(self, record):
        cd = self.conf['columns']
        string_d = {}
        for i, d in cd.items():
            # print(d['contents'])
            s = d['contents'].format(**record.__dict__)
            string_d[i] = s
        # print(string_d)
        return string_d

    # def process_output(self, d):
    #     for i in d:
    #         conf = self.conf['columns'][i]
    #         s = d[i]
    #         print(s)
    #         print(conf)
    #
    #         # Only process ANSI chars if we go over the line length.
    #         ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    #         print(len(ansi_escape.sub('', s)), conf['used_padding'])
    #
    #         l = ansiwrap.wrap(s, conf['used_padding'], break_long_words=True)
    #         ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    #
    #         # print(re.sub(ansi_escape, '', s))
    #         # print(l)
    #         # for i in l:
    #         #     print(i.encode('unicode_escape'))

    # def get_multiline_outputs(self, record):
    #     multiline_dict = {}
    #     for i, v in self.conf['columns'].items():
    #         if v['can_be_multiline']:
    #             s = v['contents_basic'].format(**record.__dict__)
    #             # print(s)
    #             if len(s) > v['used_padding']:
    #                 l = textwrap.wrap(s, v['used_padding'],
    #                                   break_long_words=True)
    #                 just = v['justify']
    #                 l = [just(TMString(x), v['used_padding']) for x in l]
    #                 for i in l:
    #                     # print(i)
    #                 multiline_dict[i] = l
    #     return multiline_dict

    # def format_single_column(self, record, column):

    def format_single_line(self, record):
        column_dict = self.conf['columns']

        formatted_string_dict = {}

        for key, c in column_dict.items():

            # Get the message components we care about first.
            record_dict = {
                k: utils.TMString(v) for k, v in record.__dict__.items()
                if k in c.fields
            }
            # print(record_dict)
            # return ''

            # Use the basic format to see if we need truncation.
            s = c.fmt_basic.format(**record_dict)
            # print(c.fmt_basic, c.reserved_padding)
            # print(s, len(s))

            # For fixed length columns, simply format
            # print(c.fmt, c.fixed_length)
            # if c.fixed_length:
            # if False:
            #     s = c.fmt.format(**record_dict)
            #     # print(s)
            #     formatted_string_dict[key] = s

            # If we need truncation
            if len(s) > c.reserved_padding:
                # print(f'{c} needs truncating')
                s = c.truncate_input(record_dict)
                # new_fmt = d['new_format']
                # new_record_dict = d['new_record_dict']
                #
                # s_full = new_fmt.format(**new_record_dict)
                # print(s)
                formatted_string_dict[key] = s

            # Else we need justification and padding
            else:
                s = c.justify_and_pad_input(record_dict)
                formatted_string_dict[key] = s

        # print(formatted_string_dict)

        separator_dict = self.conf['separators']
        # print(separator_dict)
        sd2 = {key: s.content_escaped for key, s in separator_dict.items()}
        # print(sd2)
        sd2.update(formatted_string_dict)
        template = self.conf['template']
        # print(template)
        return template.format(**sd2)

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

        # Convert any other strings
        # self.convert_log_record_properties(record)


        # d = self.get_formatted_columns(record)
        # self.process_output(d)
        # print(self.conf['columns'])
        # multilines = self.get_multiline_outputs(record)
        # print(multilines)

        s = ''

        # If the style is guaranteed a single line,
        if self.style.single_line_output:
            s = self.format_single_line(record)
            # s = self.formatMessage(record)
        # if record.exc_info:
        #     if not record.exc_text:
        #         record.exc_text = self.formatException(record.exc_info)
        # if record.exc_text:
        #     if s[-1:] != "\n":
        #         s = s + "\n"
        #     s = s + record.exc_text
        # if record.stack_info:
        #     if s[-1:] != "\n":
        #         s = s + "\n"
        #     s = s + self.formatStack(record.stack_info)
        # print(s)
        return s
