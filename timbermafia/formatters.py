import logging
import textwrap
from timbermafia.utils import *


class TMFormatter(logging.Formatter):
    """Formatter for our logging, pretty as a picture, natural splendour etc."""

    def __init__(self, *args, **kwargs):
        """Store some settings that cannot be adaptively figured out."""
        self.config = kwargs.pop('config')
        # Isolate padding settings.
        self.padding_dict = {k.replace('_padding', ''): v for k, v in self.config.items()
                             if ('padding' in k)}
        self._configured = False
        self.time_padding = None  # Will be filled adaptively
        super().__init__(*args, **kwargs)

    @property
    def columns(self):
        return self.config['columns']

    @property
    def separator(self):
        return self.config['separator']

    @property
    def levelname_padding(self):
        return len(max(list(logging._nameToLevel.keys()))) + 1

    @property
    def message_padding(self):
        return self.columns - 30 - self.time_padding

    @property
    def caller_padding(self):
        return 30

    # def set_caller_name(self, my_name):
    #     """
    #     A function to take the caller string (the bit in the log printout
    #     which tells you where the call was made) and format it, to make sure
    #     it fits the rest of the printout.
    #     """
    #     # First of all, if we are running a header, return an empty string.
    #     if 'timbermafia_decorator_divider' in my_name:
    #         return ''
    #     # If any unhelpful terms appear chuck them.
    #     terms_to_remove = ['.<module>']  # , '.__init__']
    #
    #     # Remove any leading ' root.' for class logs
    #     if my_name.startswith(' root.'):
    #         my_name = my_name[6:]
    #
    #     for term in terms_to_remove:
    #         if term in my_name:
    #             my_name = my_name.replace(term, '')
    #
    #     # If there is enough room for the full caller designation, return it.
    #     if len(my_name) <= self.caller_padding:
    #         return my_name
    #     return '...' + my_name[-self.caller_padding + 2:]

    def set_padding(self, record, s):
        """
        Get any static padding lengths that can
        be found adaptively
        """
        sections = [s.strip() for s in self._fmt.split(self.separator)]
        chunks = [chunk.strip() for chunk in s.split(self.separator)]

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
        # print(fields)

        # Space for other output
        # Separator + 2 spaces for each chunk, plus final separator
        reserved_padding = 3 * len(chunks) + 1

        for field in fields:
            reserved_padding += self.padding_dict[field]

        # Set message padding
        # print(self.columns, reserved_padding)
        self.padding_dict['message'] = self.columns - reserved_padding

        # Only run this once
        self._configured = True

    def return_padded_content(self, header, content):
        # Find the fields present
        fields = [s for s in self.padding_dict if s in header]
        # Add the padding for each field
        padding = 0
        for field in fields:
            padding += self.padding_dict[field]

        # print(fields, padding)
        # textwrap the results
        content_list = textwrap.wrap(content, padding, break_long_words=True)
        return content_list

    @staticmethod
    def clean_name(content):
        """Function to clean extraneous info from the 'name' field of LogRecords."""
        terms_to_remove = ['.<module>']
        # Remove any leading ' root.' for class logs
        # print('content:', content)
        if content.startswith('root.'):
            content = content[5:]

        for term in terms_to_remove:
            content = content.replace(term, '')
        return content

    def pad(self, header, content):
        """Function to take the individual output segments and pad them."""
        fields = [s for s in self.padding_dict if '{' + s + '}' in header]
        # Add the padding for each field
        padding = 0
        for field in fields:
            padding += self.padding_dict[field]

        # If dealing with the 'name' field, remove any excess output.
        # print(header, content)
        if ('{' + 'name' + '}') in header:
            content = self.clean_name(content)

        # If any of the components are to be truncated, do so for this content.
        truncate_list = [s for s in fields if s in self.config['truncate']]
        if truncate_list:
            if len(content) > padding:
                content = '...' + content[-padding + 3:]

        # textwrap the results
        content_list = textwrap.wrap(content, padding, break_long_words=True)
        # print(fields, padding)
        return content_list, padding

    def get_output_dict(self, partial_format_string):
        chunks = [chunk.strip() for chunk in partial_format_string.split(self.separator)]
        sections = [s.strip() for s in self._fmt.split(self.separator)]
        contents = {'max_lines': 0}
        for i, (s, c) in enumerate(zip(sections, chunks)):
            s_list, padding = self.pad(s, c)
            n_lines = len(s_list)
            if contents['max_lines'] < n_lines:
                contents['max_lines'] = n_lines
            contents[i] = {'line_array': s_list, 'padding': padding}
        return contents

    def output_dict_to_str(self, contents):
        complete_s = ''
        max_lines = contents.pop('max_lines')
        segments = len(contents)
        for i in range(max_lines):
            complete_s += self.separator + ' '
            for j in range(len(contents)):
                results = contents[j]
                try:
                    complete_s += results['line_array'][i].rjust(results['padding'])
                except IndexError:
                    complete_s += ' ' * results['padding']
                complete_s += f' {self.separator}'
                # Don't add space after final delimiter
                if j != segments - 1:
                    complete_s += ' '
            if i != max_lines - 1:
                complete_s += '\n'
        return complete_s

    def build_header(self, record):
        title = record.getMessage().center(self.columns - 2)
        return self.separator + title + self.separator

    def format(self, record):

        partial_format_string = super(TMFormatter, self).format(record)

        # If the header function is called, make a title.
        if divider_flag in partial_format_string:
            return self.columns * '-'
        if 'timbermafia_decorator_divider' in partial_format_string:
            return self.build_header(record)

        if not self._configured:
            self.set_padding(record, partial_format_string)

        d = self.get_output_dict(partial_format_string)
        s = self.output_dict_to_str(d)
        return s
