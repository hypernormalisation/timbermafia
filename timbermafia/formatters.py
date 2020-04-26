import logging
import re
import sys
import textwrap
from timbermafia.utils import *


class TMFormatter2(logging.Formatter):

    def __init__(self, fmt=None, time_fmt=None, style='%',
                 validate=False, timbermafia_style=None):

        super().__init__(fmt, time_fmt, style, validate=validate)
        self.style = timbermafia_style

    def format(self, record):
        # Convert the message string to an TMString with enhanced fmt_spec
        record.message = TMString(record.getMessage())

        # Convert the formatted ascitime string to an TMString with enhanced fmt_spec
        if self.usesTime():
            record.asctime = TMString(self.formatTime(record, self.datefmt))

        # Convert any other strings
        transform_record(record)

        s = self.formatMessage(record)
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

#
# class TMFormatStyle:
#     """For formatting Timbermafia log records."""
#
#     def __init__(self, fmt):
#         self._fmt = fmt


class TMFormatter(logging.Formatter):
    """Formatter for our logging, pretty as a picture, natural splendour etc."""

    def __init__(self, *args, **kwargs):
        """Store some settings that cannot be adaptively figured out."""
        self.config = kwargs.pop('config')
        self.jl = [self.get_header(s) for s in self.config['justify_left']]
        self.jr = [self.get_header(s) for s in self.config['justify_right']]
        self.jc = [self.get_header(s) for s in self.config['justify_center']]
        self.just_map = {
            'left': str.ljust,
            'right': str.rjust,
            'center': str.center,
        }

        # Isolate padding settings.
        self.padding_dict = {k.replace('_padding', ''): v for k, v in self.config.items()
                             if ('padding' in k)}
        self._configured = False

        # Do something hacky so that the generated logging.StrFormatStyle
        # gets our format with the substituted unique dividers.
        fmt_original = args[0]
        fmt_tm = fmt_original.replace(self.separator, replacer_flag)
        temp_args = list(args)
        temp_args[0] = fmt_tm
        args = tuple(temp_args)

        # Container for a list of the headings with the format inserted
        # so we can check for the presence of individual fields.
        self.fields_with_formats = re.findall(r'{.*?}', fmt_original)
        self.num_fields = len(self.fields_with_formats)
        self.field_warnings = []

        super().__init__(*args, **kwargs)
        self._fmt_tm = self._fmt
        self._fmt = fmt_original

    def make_format_dict(self):
        """Function to make a dict with the properties of the different
        segments of the log output."""


    @staticmethod
    def get_headers(s):
        headers = re.findall(r'{.*?}', s)
        return [x[1:-1] for x in headers]

    @property
    def columns(self):
        return self.config['columns']

    @property
    def separator(self):
        return self.config['separator']

    @property
    def show_separator(self):
        return self.config['show_separator']

    @property
    def separator_insert(self):
        if not self.show_separator:
            return ''
        return self.separator

    @property
    def line_separator(self):
        return self.config['line_separator']

    @property
    def enclose(self):
        return self.config['enclose']

    @property
    def levelname_padding(self):
        return len(max(list(logging._nameToLevel.keys()))) + 1

    def get_header(self, header):
        if self.config['format_style'] == '{':
            return '{' + header + '}'

    def set_padding(self, record, chunks):
        """
        Get any padding lengths that can
        be found adaptively
        """
        sections = [s.strip() for s in self._fmt.split(self.separator)]
        print(sections)
        # chunks = [chunk.strip() for chunk in s.split(self.separator)]

        # Set timestamp padding
        if 'asctime' in self._fmt:
            for section, message in zip(sections, chunks):
                if 'asctime' in section:
                    tp = len(message)
                    self.padding_dict['asctime'] = tp

        # Set levelname padding
        self.padding_dict['levelname'] = self.levelname_padding

        # Set message padding, i.e. the rest of the space
        fields = [s for s in self.padding_dict if s in self._fmt]

        # Space for other output
        # Separator + 2 spaces for each chunk, plus final separator
        reserved_padding = 3 * len(chunks) + 1
        if not self.show_separator:
            reserved_padding = 2 * len(chunks) + 1

        for field in fields:
            reserved_padding += self.padding_dict[field]

        # Set message padding
        message_padding = self.columns - reserved_padding
        if not self.enclose:
            message_padding += 4
        self.padding_dict['message'] = message_padding

        self.build_segment_dict()

        # Only run this once
        self._configured = True

    def build_segment_dict(self):
        pass
        # print(self.fields_with_formats)

    def return_padded_content(self, header, content):
        # Find the fields present
        fields = [s for s in self.padding_dict if s in header]
        # Add the padding for each field
        padding = 0
        for field in fields:
            padding += self.padding_dict[field]

        # textwrap the results
        content_list = textwrap.wrap(content, padding, break_long_words=True)
        return content_list

    @staticmethod
    def clean_name(content):
        """Function to clean extraneous info from the 'name' field of LogRecords."""
        terms_to_remove = ['.<module>']
        # Remove any leading ' root.' for class logs
        if content.startswith('root.'):
            content = content[5:]

        for term in terms_to_remove:
            content = content.replace(term, '')
        return content

    def justify_contents(self, header, content_list, padding):
        # print(header, content_list)
        just = self.config['justify']
        active_headers = self.get_headers(header)
        # print(active_headers)
        modifiers = []
        for section in active_headers:
            if section in self.jl:
                modifiers.append('left')
            if section in self.jr:
                modifiers.append('right')
            if section in self.jc:
                modifiers.append('center')
        if modifiers:
            if len(modifiers) > 1 and header not in self.field_warnings:
                print('WARNING: multiple justification modifiers present for '
                      f'section: {header}, defaulting to {modifiers[0]} justification.')
                self.field_warnings.append(header)
            just = modifiers[0]
        # print(content_list)
        new_contents = []
        for line in content_list:
            new_contents.append(self.just_map[just](line, padding))
        return new_contents

    def wrap_and_pad_text(self, header, content):
        """Function to take the individual output
         segments and assign padding.

         Does not pad the contents itself.
         """
        fields = [s for s in self.padding_dict if '{' + s + '}' in header]
        # Add the padding for each field
        padding = 0
        for field in fields:
            padding += self.padding_dict[field]

        # If dealing with the 'name' field, remove any excess output.
        if (self.get_header('name')) in header:
            if self.config['clean_names']:
                content = self.clean_name(content)

        # If any of the components are to be truncated, do so for this content.
        truncate_list = [s for s in fields if s in self.config['truncate']]
        if truncate_list:
            if len(content) > padding:
                content = '...' + content[-padding + 3:]

        # textwrap the results
        content_list = textwrap.wrap(content, padding, break_long_words=True)

        # justify the results
        content_list = self.justify_contents(header, content_list, padding)

        return content_list, padding

    def get_output_dict(self, chunks):
        """Generate a dict containing line arrays using the specified paddings."""
        # chunks = [chunk.strip() for chunk in partial_format_string.split(self.separator)]
        sections = [s.strip() for s in self._fmt.split(self.separator)]
        contents = {'max_lines': 0}
        for i, (s, c) in enumerate(zip(sections, chunks)):
            s_list, padding = self.wrap_and_pad_text(s, c)
            n_lines = len(s_list)
            if contents['max_lines'] < n_lines:
                contents['max_lines'] = n_lines
            contents[i] = {'line_array': s_list, 'padding': padding, 'section': s}

        # Now pad the lines

        return contents

    def output_dict_to_str(self, contents):
        """Convert the dict containing the line arrays to a final string."""
        complete_s = ''
        # max_lines = contents.pop('max_lines')
        max_lines = contents['max_lines']
        num_segments = len(contents) - 1
        # print(contents)
        to_iter = max_lines
        # if self.config['divide_lines']:
        #     to_iter = max_lines + 1
        for line_number in range(to_iter):
            for j in range(num_segments):
                if j == 0 and self.enclose:
                    # if line_number != 0 and self.config['sparse_separators']:
                    #     complete_s += '  '
                    # else:
                    complete_s += self.separator_insert + ' '
                results = contents[j]
                try:
                    complete_s += results['line_array'][line_number]
                except IndexError:
                    # if i == to_iter - 1:
                    #     # complete_s = complete_s[:-1]
                    #     complete_s += self.line_separator * (results['padding'])
                    # else:
                    complete_s += ' ' * results['padding']

                # if i != to_iter - 1:

                #     if i != 1 and j < len(contents):
                #         complete_s += '  '
                # else:
                if self.config['sparse_separators'] and \
                        line_number > 0 and j != len(contents)-2:
                    complete_s += '  '
                    # print(len(contents))
                else:
                    complete_s += f' {self.separator_insert}'
                #
                if j != num_segments - 1:
                    complete_s += ' '
                # else:

                # Don't add space after final delimiter

            # Trim separator as needed.
            if not self.enclose:
                to_trim = 1 + len(self.separator)
                complete_s = complete_s[:-to_trim]

            elif self.config['sparse_separators']:
                complete_s = complete_s[:-1]
                complete_s += self.separator_insert

            # Linebreak for all but the last line.
            if line_number != to_iter - 1:
                complete_s += '\n'

        return complete_s

    def build_header(self, record):
        """Build a center justified title."""
        title = record.getMessage().center(self.columns - 2)
        return self.separator + title + self.separator

    @property
    def line_separator_string(self):
        s = self.line_separator * self.columns
        s = s[:self.columns]
        return s

    def enclose_frame(self, s):
        """Function to enclose the frame as required."""
        if not self.config['enclosers']:
            line_list = s.split('\n')
            new_list = []
            for line in line_list:
                line += self.separator_insert
                line = self.separator_insert + line
                print(line)
                new_list.append(line)
            s = '\n'.join(new_list)
        else:
            sys.exit('NOT IMPLEMENTED')
            # if len(self.config['enclosers']) == 1:
            #     s += self.config['enclosers'] * 2
            # else:
            #     s += self.config['enclosers']
        return s

    def build_fields(self, complete_s, contents):
        num_lines = contents['max_lines']
        # if self.config['divide_lines']:
        #     to_iter = max_lines + 1
        # max_lines = contents['max_lines']
        num_segments = len(contents) - 1

        sparse = self.config['sparse_separators']
        for line_number in range(num_lines):
            for j in range(num_segments):



                # if j == 0 and self.enclose:
                #     # if line_number != 0 and self.config['sparse_separators']:
                #     #     complete_s += '  '
                #     # else:
                #     complete_s += self.separator_insert + ' '

                if self.config['sparse_separators'] and \
                        line_number > 0 and j != len(contents) - 2:
                    complete_s += '  '
                else:
                    complete_s += f' {self.separator_insert}'
                #
                if j != num_segments - 1:
                    complete_s += ' '

            # # Trim separator as needed.
            # if not self.enclose:
            #     to_trim = 1 + len(self.separator)
            #     complete_s = complete_s[:-to_trim]

            # elif self.config['sparse_separators']:
            #     complete_s = complete_s[:-1]
            #     complete_s += self.separator_insert

            # Linebreak for all but the last line.
            if line_number != num_lines - 1:
                complete_s += '\n'

        return complete_s

    def build_frame(self, d):
        s = ''
        s = self.build_fields(s, d)

        # If necessary enclose
        if self.enclose:
            s = self.enclose_frame(s)

        print('Frame says:', s)
        print(self._fmt_tm)
        return s

    def format(self, record):
        partial_format_string = super(TMFormatter, self).format(record)
        record_components = partial_format_string.split(replacer_flag)
        record_components = [x.lstrip().rstrip() for x in record_components]

        # If the header function is called, make a title.
        if divider_flag in partial_format_string:
            return self.line_separator_string
        if header_flag in partial_format_string:
            return self.build_header(record)

        if not self._configured:
            self.set_padding(record, record_components)

        # Pad the components and return the config in a dict.
        d = self.get_output_dict(record_components)
        print(d)

        # s = self.output_dict_to_str(d)

        s = self.build_frame(d)

        # if self.config['divide_lines']:
        #     s += '\n' + self.line_separator_string

        return s
