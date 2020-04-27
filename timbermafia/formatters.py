import ansiwrap
import logging
import re
import shutil
import string
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

    def get_multiline_outputs(self, record):
        multiline_dict = {}
        for i, v in self.conf['columns'].items():
            if v['can_be_multiline']:
                s = v['contents_basic'].format(**record.__dict__)
                print(s)
                if len(s) > v['used_padding']:
                    l = textwrap.wrap(s, v['used_padding'],
                                      break_long_words=True)
                    just = v['justify']
                    l = [just(TMString(x), v['used_padding']) for x in l]
                    for i in l:
                        print(i)
                    multiline_dict[i] = l
        return multiline_dict

    def format_single_line(self, record):
        cd = self.conf['columns']
        string_d = {}
        for newkey, (i, d) in zip(string.ascii_uppercase, cd.items()):
            # print(d['contents'])
            s = d['contents'].format(**record.__dict__)
            just = d['justify']
            string_d[newkey] = just(s, d['used_padding'])
        print(string_d)

        sd = self.conf['separators']
        print(sd)
        sd2 = {k: v['contents'] for k, v in sd.items()}
        print(sd2)
        sd2.update(string_d)
        template = self.conf['template']
        template = '{A} {a} {B} {b} {C} {c} {D}'
        print(template)
        return template.format(**sd2)


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


        # d = self.get_formatted_columns(record)
        # self.process_output(d)
        print(self.conf['columns'])
        multilines = self.get_multiline_outputs(record)
        print(multilines)

        s = ''
        if not multilines:
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
