import logging
import re
import shutil
import sys
import textwrap
from timbermafia.utils import *


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

    def format_columns(self, record):
        cd = self.conf['columns']
        string_d = {}
        for i, d in cd.items():
            # print(d['contents'])
            s = d['contents'].format(**record.__dict__)
            string_d[i] = s
        print(string_d)

    def format(self, record):

        # If there is no timbermafia style, defer to Formatter.format
        if not self.style:
            return super().format(record)

        # Convert the message string to an TMString with enhanced fmt_spec
        record.message = TMString(record.getMessage())

        # Convert the formatted ascitime string to an TMString with enhanced fmt_spec
        if self.usesTime():
            record.asctime = TMString(self.formatTime(record, self.datefmt))

        # Convert any other strings
        transform_record(record)
        self.format_columns(record)

        s = self.formatMessage(record)
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
