"""
Tests for pytest to ensure that logging levels (INFO, DEBUG etc...) are
being respected.
"""
import logging
import pytest
import timbermafia as tm


class MyTestClass(tm.Logged):
    """Non-test class to check class loggers are functioning."""
    def __init__(self):

        self.log_map = {
            logging.DEBUG: {
                'func': self.output_debug,
                'output': 'DEBUG output from class',
            },
            logging.INFO: {
                'func': self.output_info,
                'output': 'INFO output from class',
            },
            logging.WARNING: {
                'func': self.output_warning,
                'output': 'WARNING output from class',
            },
            logging.ERROR: {
                'func': self.output_error,
                'output': 'ERROR output from class',
            },
            logging.CRITICAL: {
                'func': self.output_critical,
                'output': 'CRITICAL output from class',
            },
        }

    def call_log(self, level):
        self.log_map[level]['func']()

    def output_debug(self):
        self.log.debug(self.get_output(logging.DEBUG))

    def output_info(self):
        self.log.info(self.get_output(logging.INFO))

    def output_warning(self):
        self.log.warning(self.get_output(logging.WARNING))

    def output_error(self):
        self.log.error(self.get_output(logging.ERROR))

    def output_critical(self):
        self.log.critical(self.get_output(logging.CRITICAL))

    def get_output(self, level):
        return self.log_map[level]['output']


@pytest.mark.parametrize("class_level", [
    logging.DEBUG, logging.INFO,
    logging.WARNING, logging.ERROR, logging.CRITICAL,
])
@pytest.mark.parametrize("global_level", [
    logging.DEBUG, logging.INFO,
    logging.WARNING, logging.ERROR, logging.CRITICAL,
])
@pytest.mark.parametrize("log_name", [None, 'my_test'])
def test_class_levels(class_level, global_level, log_name, capsys):
    """Checks that the class log is picked up and its level
    is being properly respected.
    """
    tm.basic_config(name=log_name, level=logging.DEBUG)
    t = MyTestClass()

    # Change the log level up and down
    t.log.setLevel(logging.CRITICAL)
    t.log.setLevel(global_level)

    t.call_log(class_level)
    out, err = capsys.readouterr()
    if class_level >= global_level:
        assert t.get_output(class_level) in out
    else:
        assert t.get_output(class_level) not in out


@pytest.mark.parametrize("log_level", [
    logging.DEBUG, logging.INFO,
    logging.WARNING, logging.ERROR, logging.CRITICAL,
])
@pytest.mark.parametrize("global_level", [
    logging.DEBUG, logging.INFO,
    logging.WARNING, logging.ERROR, logging.CRITICAL,
])
@pytest.mark.parametrize("log_name", [None, 'my_test'])
def test_global_levels(log_level, global_level, log_name, capsys):
    """Checks that named logs respect the level conventions set."""
    tm.basic_config(clear=True, name=log_name)
    log_name_manual = 'my_test'
    log = logging.getLogger(log_name_manual)
    log_map = {
        logging.DEBUG: {
            'func': log.debug,
            'output': 'DEBUG output from class',
        },
        logging.INFO: {
            'func': log.info,
            'output': 'INFO output from class',
        },
        logging.WARNING: {
            'func': log.warning,
            'output': 'WARNING output from class',
        },
        logging.ERROR: {
            'func': log.error,
            'output': 'ERROR output from class',
        },
        logging.CRITICAL: {
            'func': log.critical,
            'output': 'CRITICAL output from class',
        },
    }
    # Change the log level up and down
    log.setLevel(logging.CRITICAL)
    log.setLevel(global_level)

    f = log_map[log_level]['func']
    expected_output = log_map[log_level]['output']
    f(expected_output)

    out, err = capsys.readouterr()

    if log_level >= global_level:
        assert expected_output in out
    else:
        assert expected_output not in out
