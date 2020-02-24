import logging
import textwrap
from timbermafia.utils import *


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

        # Do something hacky so that the generator logging.StrFormatStyle
        # gets our format with the substituted unique dividers.
        fmt_original = args[0]
        fmt_tm = fmt_original.replace(self.separator, replacer_flag)
        temp_args = list(args)
        temp_args[0] = fmt_tm
        args = tuple(temp_args)
        self.time_padding = None  # Will be filled adaptively
        super().__init__(*args, **kwargs)
        self._fmt = fmt_original

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
        Get any static padding lengths that can
        be found adaptively
        """
        sections = [s.strip() for s in self._fmt.split(self.separator)]
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

        # Only run this once
        self._configured = True

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

    def pad(self, header, content):
        """Function to take the individual output segments and pad them."""
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
        # print(content_list)
        return content_list, padding

    def get_output_dict(self, chunks):
        """Generate a dict containing line arrays using the specified paddings."""
        # chunks = [chunk.strip() for chunk in partial_format_string.split(self.separator)]
        sections = [s.strip() for s in self._fmt.split(self.separator)]
        contents = {'max_lines': 0}
        for i, (s, c) in enumerate(zip(sections, chunks)):
            s_list, padding = self.pad(s, c)
            n_lines = len(s_list)
            if contents['max_lines'] < n_lines:
                contents['max_lines'] = n_lines
            contents[i] = {'line_array': s_list, 'padding': padding, 'section': s}
        # print(contents)
        return contents

    def output_dict_to_str(self, contents):
        """Convert the dict containing the line arrays to a final string."""
        complete_s = ''
        max_lines = contents.pop('max_lines')
        segments = len(contents)
        # print(contents)
        to_iter = max_lines
        # if self.config['divide_lines']:
        #     to_iter = max_lines + 1
        for line_number in range(to_iter):
            for j in range(len(contents)):
                if j == 0 and self.enclose:
                    # if line_number != 0 and self.config['sparse_separators']:
                    #     complete_s += '  '
                    # else:
                    complete_s += self.separator_insert + ' '
                results = contents[j]
                try:
                    # Figure out how to justify this output.
                    section = results['section']
                    just = self.config['justify']
                    if section in self.jl:
                        complete_s += results['line_array'][line_number].ljust(results['padding'])
                    elif section in self.jr:
                        complete_s += results['line_array'][line_number].rjust(results['padding'])
                    elif section in self.jc:
                        complete_s += results['line_array'][line_number].center(results['padding'])
                    else:
                        complete_s += self.just_map[just](results['line_array'][line_number],
                                                          results['padding'])
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
                if j != segments - 1:
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

        d = self.get_output_dict(record_components)
        s = self.output_dict_to_str(d)

        if self.config['divide_lines']:
            s += '\n' + self.line_separator_string

        return s
