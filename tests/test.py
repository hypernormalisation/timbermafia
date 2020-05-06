import logging
import timbermafia as tm
import time
import sys

f = '{asctime:u} _ {levelname} _ {name}.{funcName} __>> {message:b,>15}'
tm.basic_config(format=f, palette='synth', silent=True)

# tm.basic_config(palette='synth')

st = 'This is a very long message that will be split over \
multiple lines in a sensible output width. Column alignments can make' \
     ' reading such long text in the middle of a crowded log output' \
     ' a little easier for the user.'

log = logging.getLogger(__name__)
log.info('Logging from main body of test script')


class MyClass(tm.Logged):
    """Demo class showing how to use a timbermafia mixin logger."""
    def test_function(self):
        self.log.info(st)
        self.log.debug('This is DEBUG output.')
        self.log.warning('This is WARNING output.')
        self.log.error('This is ERROR output.')
        self.log.critical('This is CRITICAL output.')

    def function_with_a_very_very_long_name(self):
        self.log.info('Long output, e.g case function names, can be truncated.')
        # self.log.debug('A url looks like https://github.com and is different?')
        # self.log.warning('A filename like /tmp/test.db looks like this or like'
        #                  ' /tmp/test2.db for 2 matches to find')


A = MyClass()


while True:
    A.test_function()
    A.function_with_a_very_very_long_name()
    sys.exit()
    # time.sleep(2.5)

