import logging
import timbermafia
import sys

lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor " \
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud " \
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute " \
        "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " \
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia " \
        "deserunt mollit anim id est laborum. "


class MyClass(timbermafia.Logged):
    def status(self):
        self.log.info(f'logging from {self.__class__.__name__} in the function status')

my_palette = 'sensible'
if len(sys.argv) > 1:
    my_palette = sys.argv[1]
timbermafia.configure(palette=my_palette,
                      format='{asctime} | {levelname} | {name}.{funcName} | {message}')
timbermafia.add_handler(stream=sys.stdout, filename='/tmp/my.log')

log = logging.getLogger(__name__)

log.header('Demo of timbermafia logging')
log.info(lorem)
m = MyClass()
m.status()
log.debug('Some debug output with a url: www.github.com')
log.warning('Some warning with a local file: /tmp/some.db')
log.error('Here is an error.')
log.fatal('Fatal error encountered')
# log.critical('Critical error encountered')
