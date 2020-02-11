import logging
import timbermafia
import sys

lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor " \
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud " \
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute " \
        "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " \
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia " \
        "deserunt mollit anim id est laborum. "

timbermafia.configure_root_logger(
    style='test1', stream=sys.stdout, filename='/tmp/test.log'
)

log = logging.getLogger(__name__)

log.hinfo('Test of timbermafia logging')
log.info(lorem)
log.debug('Some debug output with a url: www.google.com')
log.warning('Some warning with a local file: /tmp/some.db')
print('I should have no colour.')

# RED = "\033[38;5;203m"
# ORANGE = "\033[38;5;214m"
# print(RED + 'some red text ' + ORANGE + 'some other text')