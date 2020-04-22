import re

TEMPLATE = '\033[{}m'
BOLD = '\033[1m'
EMPH = '\33[3m'
RESET = '\033[0m'
UNDERLINE = '\033[4m'

alpha_pattern = re.compile('[a-zA-Z]*')
numeric_pattern = re.compile('[0-9]*')
both_pattern = re.compile('[A-Za-z0-9]*([a-zA-Z]+[0-9]+|[0-9]+[a-zA-Z]+)')

class TMString(str):

    def __init__(self, content):
        self.content = content
        super().__init__()

    @staticmethod
    def _format_alpha_spec(s, fmt_spec):
        params_list = []
        if 'b' in fmt_spec:
            params_list.append(BOLD)
        if 'e' in fmt_spec:
            params_list.append(EMPH)
        if 'u' in fmt_spec:
            params_list.append(UNDERLINE)
        return params_list

    @staticmethod
    def _format_number_spec(s, fmt_spec):
        return '\033[' + fmt_spec + 'm'

    def __format__(self, fmt_spec=''):
        printable = ''
        params = []
        if fmt_spec:

            # Remove whitspace
            fmt_spec.replace(' ', '')

            fmts = fmt_spec.split(',')

            # First separate any number/letter combos
            parsed_fmts = []
            for fmt in fmts:
                if not fmt.isalnum():
                    raise ValueError('fmt_spec is not alphanumeric')
                # If both numbers and letters are present separate them
                if both_pattern.match(fmt):
                    characters = [x for x in alpha_pattern.findall(fmt) if x]
                    numbers = [x for x in numeric_pattern.findall(fmt) if x]
                    for x in numbers+characters:
                        parsed_fmts.append(x)
                else:
                    parsed_fmts.append(fmt)

            for fmt in parsed_fmts:
                if fmt.isnumeric():
                    params.append(self._format_number_spec(printable, fmt))
                elif fmt.isalpha():
                    plist = self._format_alpha_spec(printable, fmt)
                    for p in plist:
                        params.append(p)
        return "".join(
            ("".join(params), self.content, RESET)
        )

#
# s = TMString('I am a TMString')
# print(s)
# print(s.encode('unicode_escape'))
#
# print(f'{s:bu,7}'.encode('unicode_escape'))
# print(f'{s:7b}')
# print(f'{s:bu51,1}')
# print('I am a regular old string')
