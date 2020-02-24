divider_flag = 'ab9367b3-d977-44ec-bce7-fef40aa4428d'
header_flag = 'timbermafia_header_04ce0a20e181'
replacer_flag = 'timbermafia_replacer_f0df7d32d480'
LOCALFILE = 'file'
URL = 'url'


def divider():
    return divider_flag


def run_from_ipython():
    try:
        # noinspection PyUnresolvedReferences
        __IPYTHON__
        return True
    except NameError:
        return False

#
# def headed_log(func):
#     """A decorator for header breaks in stdout."""
#     def timbermafia_decorator_divider(self, *args, **kwargs):
#         print(*args)
#         self.func(divider())
#         self.func(*args, **kwargs)
#         self.func(divider())
#     return timbermafia_decorator_divider
