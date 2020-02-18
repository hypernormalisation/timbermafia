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
        return len(max(list(logging._nameToLevel.keys())))

    @property
    def message_padding(self):
        return self.columns - 30 - self.time_padding

    @property
    def caller_padding(self):
        return 30

    def set_caller_name(self, my_name):
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
        if len(my_name) <= self.caller_padding:
            return my_name
        return '...' + my_name[-self.caller_padding + 2:]

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

        # Set message padding, i.e. the rest of the space
        fields = [s for s in self.padding_dict if s in self._fmt]
        print(fields)

        # Space for delimiters
        reserved_padding = 2 * len(fields)

        for field in fields:
            reserved_padding += self.padding_dict[field]

        # Set message padding
        self.padding_dict['message'] = self.columns - reserved_padding

        self._configured = True

    def return_padded_content(self, header, content):
        # Find the fields present
        fields = [s for s in self.padding_dict if s in header]
        # Add the padding for each field
        padding = 0
        for field in fields:
            padding += self.padding_dict[field]

            # # Calculate length of any other strings in format
            # hc = header[:]
            # if '{' in header:
            #     hc = hc.replace('{', '')
            #     hc = hc.replace('}', '')
            # for field in fields:
            #     hc = hc.replace(field, '')

        print(fields, padding)
        # textwrap the results
        content_list = textwrap.wrap(content, padding, break_long_words=True)
        return content_list

    def format(self, record):

        show_level_name = 'levelname' in self._fmt

        s = super(TMFormatter, self).format(record)
        if not self._configured:
            self.set_padding(record, s)

        if divider_flag in s:
            s = self.columns * '-'
            return s

        # If we don't have the time padding, figure it out.
        # if not self.time_padding:
        #     sections = [s.strip() for s in self._fmt.split(self.separator)]
        #     chunks = [chunk.strip() for chunk in s.split(self.separator)]
        #     for section, message in zip(sections, chunks):
        #         # print(f'{section}: {message}')
        #         # Length of time string will be uniform so adaptively read it.
        #         if 'asctime' in section:
        #             self.time_padding = len(message) + 2

        # if '\nTraceback (most recent call last)' in s:
        #     print(s)

        split_list = s.split(self.separator)
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
        s_list = textwrap.wrap(print_statement, self.message_padding - 3,
                               break_long_words=True)

        # Now we need to construct each individual printout string from the time,
        # caller, and print info.
        for index, printout in enumerate(s_list):
            # If it's the first line, add the timestamp and caller.
            if index == 0:
                # pad the caller name to be the required length
                caller_name = caller_name.rjust(self.caller_padding + 1)
                the_string = timestamp + '| ' + caller_name + '|' + printout
            else:
                the_string = (len(timestamp) * ' ' + '| ' +
                              ''.rjust(self.caller_padding + 1) + '| ' + printout)
            s_list[index] = the_string

        s = '\n'.join(s_list).strip(" ")
        return s