divider_flag = 'ab9367b3-d977-44ec-bce7-fef40aa4428d'


def divider():
    return divider_flag


def run_from_ipython():
    try:
        # noinspection PyUnresolvedReferences
        __IPYTHON__
        return True
    except NameError:
        return False


def headed_log(func):
    """A decorator for header breaks in stdout."""
    def decorator_divider(self, *args, **kwargs):
        func(divider())
        func(*args, **kwargs)
        func(divider())
    return decorator_divider