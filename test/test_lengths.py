"""
Tests for pytest to ensure proper lengths and format in
the configuration are respected.

Should cover cases where we have manual widths, max widths, fit_to_terminal etc.
"""
import logging
import shutil
import timbermafia as tm
import timbermafia.utils as utils
import timbermafia.styles

short_string = 'Some sample message.'

long_string = 'A very long message that will have to be split over multiple' \
    'lines, that will be used in testing multiline printout in this module.'

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


def test_manual_width_small(capsys):
    """Test the lower limit of the width setting."""
    w = 40
    tm.basic_config(width=w)
    log = logging.getLogger()
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


def test_manual_width_high(capsys):
    """Test an arbitrarily high width setting."""
    w = 200
    tm.basic_config(width=w)
    log = logging.getLogger()
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


# def test_low_max_width_with_fit_to_terminal(capsys):
#     """Test to ensure a max width is respected with fit_to_terminal
#     enabled. Will only test what it's supposed to if terminal width is above 60,
#     else it just tests max_width."""
#     w = 60
#     style = tm.generate_default_style()
#     style.fit_to_terminal = True
#     style.max_width = w
#
#     n_columns = shutil.get_terminal_size().columns
#     assert n_columns == 80
#     if n_columns < w:
#         w = n_columns
#
#     tm.basic_config(style=style)
#     log = logging.getLogger()
#     log.info(short_string)
#     out, err = capsys.readouterr()
#     line = out.split('\n')[-2]
#     line = utils.strip_ansi_codes(line)
#
#     assert len(line) == w


def test_high_max_width_with_fit_to_terminal(capsys):
    """Test to ensure a max width is respected with fit_to_terminal
    enabled."""
    w = 200
    style = tm.generate_default_style()
    style.fit_to_terminal = True
    style.max_width = w

    n_columns = shutil.get_terminal_size().columns
    assert n_columns == 80
    if n_columns < w:
        w = n_columns

    tm.basic_config(style=style)
    log = logging.getLogger()
    log.info(short_string)
    out, err = capsys.readouterr()
    line = out.split('\n')[-2]
    line = utils.strip_ansi_codes(line)

    assert len(line) == w