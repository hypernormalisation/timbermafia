"""
Tests for pytest to ensure proper lengths and format in
the configuration are respected.
"""
import logging
import shutil
import pytest
import timbermafia as tm
import timbermafia.utils as utils
import timbermafia.styles

short_string = 'Some sample message.'

long_string = 'A very very very very very very very very very very very very' \
              'long message that will have to be split over multiple' \
              'lines, that will be used in testing multiline printout in ' \
              'this module.'

default_length = timbermafia.styles._style_defaults['width']


def preconfigure():
    tm.basic_config(clear=True)
    return logging.getLogger()


def test_single_line_default(capsys):
    """Test to ensure the length of a short,
    single line under the default settings.
    """
    log = preconfigure()
    log.info(short_string)
    out, err = capsys.readouterr()
    last_line = out.split('\n')[-2]
    last_line_no_ansi = utils.strip_ansi_codes(last_line)

    assert len(last_line_no_ansi) == default_length


def test_multi_line_default(capsys):
    """Test to ensure the length of a multi-line string
    under the default settings."""
    log = preconfigure()
    log.info(long_string)
    out, err = capsys.readouterr()
    first_line = out.split('\n')[-3]
    first_line_no_ansi = utils.strip_ansi_codes(first_line)
    last_line = out.split('\n')[-2]
    last_line_no_ansi = utils.strip_ansi_codes(last_line)

    assert len(first_line_no_ansi) == default_length
    assert len(last_line_no_ansi) == default_length


@pytest.mark.parametrize("log_width", list(range(40, 200, 3)))
@pytest.mark.parametrize("log_name", [None, 'my_test'])
def test_manual_width(log_width, log_name, capsys):
    """Test the width setting."""
    w = log_width
    tm.basic_config(width=w)
    log_name_manual = 'my_test'
    log = logging.getLogger(log_name_manual)
    log.info(short_string)
    out, err = capsys.readouterr()
    line = out.split('\n')[-2]
    line = utils.strip_ansi_codes(line)
    assert len(line) == w

    log.debug(long_string)
    out, err = capsys.readouterr()
    line_first = out.split('\n')[-3]
    line_first = utils.strip_ansi_codes(line_first)

    line_last = out.split('\n')[-2]
    line_last = utils.strip_ansi_codes(line_last)

    assert len(line_first) == w
    assert len(line_last) == w


def test_fit_to_terminal(capsys):
    """Test that the terminal width is respected."""
    tm.basic_config(fit_to_terminal=True)
    log = logging.getLogger()
    log.info(short_string)

    out, err = capsys.readouterr()
    line = out.split('\n')[-2]
    line = utils.strip_ansi_codes(line)
    n_columns = shutil.get_terminal_size().columns

    assert len(line) == n_columns
