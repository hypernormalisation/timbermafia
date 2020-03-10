import logging
import timbermafia
import sys
import argparse

parser = argparse.ArgumentParser('timbermafia styles/palettes')

parser.add_argument('--style', '-s', type=str, choices=timbermafia.style_map.keys(),
                    help='timbermafia style to use for formatting',
                    default='default')
parser.add_argument('--palette', '-p', type=str, choices=timbermafia._valid_palettes,
                    help='timbermafia palette to use for formatting',
                    default='sensible')

lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor " \
        "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud " \
        "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute " \
        "irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla " \
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia " \
        "deserunt mollit anim id est laborum."


class MyClass(timbermafia.Logged):
    def status(self):
        self.log.info(f'logging from {self.__class__.__name__} in the function status')

my_args = parser.parse_args()
my_palette = my_args.palette
my_style = my_args.style

timbermafia.configure(palette=my_palette, style=my_style, enclose=True)
                      # format='{asctime} | {levelname} | {name}.{funcName} | {message}')
timbermafia.add_handler(stream=sys.stdout) #, filename='/tmp/timbermafia_test.log')

log = logging.getLogger(__name__)

# log.header('Demo of timbermafia logging')
log.info('INFO messages look like this')
# log.info('urls look like this: www.github.com or https://ipleak.net/')
# log.info('local files look like this: /tmp/timbermafia_test.log '
#          '- this output is being written there too!')
# log.info(lorem)
#
# m = MyClass()
# m.log.info('messages from MyClass with a timbermafia mixin logger look like this')
# m.status()
# log.debug('DEBUG messages look like this')
# log.warning('WARNING messages look like this')
# log.error('ERROR messages look like this')
# log.fatal('FATAL/CRITICAL error messages look like this.')
