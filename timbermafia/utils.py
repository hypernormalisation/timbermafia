import re

TEMPLATE = '\033[{}m'
BOLD = '\033[1m'
EMPH = '\33[3m'
RESET = '\033[0m'
UNDERLINE = '\033[4m'

alpha_pattern = re.compile('[a-zA-Z]*')
numeric_pattern = re.compile('[0-9]*')
both_pattern = re.compile('[A-Za-z0-9]*([a-zA-Z]+[0-9]+|[0-9]+[a-zA-Z]+)')
column_sep_pattern = re.compile(r'_{1,2}\S+|_{1,2}')
logrecord_component_pattern = re.compile(r'(?<={)[a-zA-Z]+(?=[}:])')
logrecord_present_pattern = re.compile(r'.*{\w+(:\S+)?}.*')


fg_escape = '>'
bg_escape = '<'


def strip_ansi_codes(s):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', s)


class TMString(str):
    """String subclass to include a fmt_spec, to be used in log formatting."""
    def __init__(self, content):
        self.content = str(content)
        super().__init__()

    @staticmethod
    def _format_alpha_spec(fmt_spec):
        """Parse any alphabetical flags in the fmt_spec."""
        params_list = []
        if 'b' in fmt_spec:
            params_list.append(BOLD)
        if 'e' in fmt_spec:
            params_list.append(EMPH)
        if 'u' in fmt_spec:
            params_list.append(UNDERLINE)
        return params_list

    @staticmethod
    def _format_number_spec(fmt_spec):
        """Parse any numeric flags and convert
        them to the appropriate escape code"""
        return '\033[' + fmt_spec + 'm'

    @staticmethod
    def _format_foreground_colour(fmt_spec):
        return '\033[38;5;' + fmt_spec.replace(fg_escape, '') + 'm'

    @staticmethod
    def _format_background_colour(fmt_spec):
        return '\033[48;5;' + fmt_spec.replace(bg_escape, '') + 'm'

    def __format__(self, fmt_spec=''):
        """Add a flexible format spec that supports any ANSI escape codes
        including colours."""
        if not fmt_spec:
            return self.content
        params = [RESET]
        # Remove whitespace
        fmt_spec.replace(' ', '')
        fmts = fmt_spec.split(',')

        parsed_fmts = []
        for fmt in fmts:

            # First format foreground and background colours as needed
            if re.search(fg_escape, fmt):
                params.append(self._format_foreground_colour(fmt))
            if re.search(bg_escape, fmt):
                params.append(self._format_background_colour(fmt))

            # If both numbers and letters are present separate them
            elif both_pattern.match(fmt):
                characters = [x for x in alpha_pattern.findall(fmt) if x]
                numbers = [x for x in numeric_pattern.findall(fmt) if x]
                for x in numbers+characters:
                    parsed_fmts.append(x)
            else:
                parsed_fmts.append(fmt)

        for fmt in parsed_fmts:
            if fmt.isnumeric():
                params.append(self._format_number_spec(fmt))
            elif fmt.isalpha():
                plist = self._format_alpha_spec(fmt)
                for p in plist:
                    params.append(p)

        # Reset the fmt_spec
        if params:
            return "".join(
                ("".join(params), self.content, RESET)
            )
        else:
            return self.content
