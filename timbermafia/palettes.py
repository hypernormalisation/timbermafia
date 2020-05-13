"""Colour palettes for timbermafia.

Users can generate their own Palette classes and customise them, for use
within timbermafia's framework or more generally in python logging
"""

import collections.abc
import logging
import timbermafia.utils as utils

# Preset colour palettes using 8-bit ANSI codes.
_sensible = {
    logging.DEBUG: {'fg': 33},
    logging.INFO: {'fg': 255},
    logging.WARNING: {'fg': 214},
    logging.ERROR: {'fg': 196, 'codes': 1},
    logging.FATAL: {'fg': 40, 'bg': 52, 'codes': 1},
}

_sensible_light = {
    logging.DEBUG: {'fg': 18},
    logging.INFO: {'fg': 232},
    logging.WARNING: {'fg': 130},
    logging.ERROR: {'fg': 196, 'codes': 1},
    logging.FATAL: {'fg': 40, 'bg': 52, 'codes': 1},
}

_forest = {
    logging.DEBUG: {'fg': 22},
    logging.INFO: {'fg': 34},
    logging.WARNING: {'fg': 202},
    logging.ERROR: {'fg': 94, 'codes': 1},
    logging.FATAL: {'fg': 0, 'bg': 94, 'codes': 1},
}

_ocean = {
    logging.DEBUG: {'fg': 27},
    logging.INFO: {'fg': 45},
    logging.WARNING: {'fg': 47},
    logging.ERROR: {'fg': 226, 'codes': 1},
    logging.FATAL: {'fg': 226, 'bg': 18, 'codes': 1},
}

_synth = {
    logging.DEBUG: {'fg': 51},
    logging.INFO: {'fg': 201},
    logging.WARNING: {'fg': 225},
    logging.ERROR: {'fg': 213, 'codes': 1},
    logging.FATAL: {'fg': 44, 'bg': 57, 'codes': 1},
}

_dawn = {
    logging.DEBUG: {'fg': 200},
    logging.INFO: {'fg': 208},
    logging.WARNING: {'fg': 190},
    logging.ERROR: {'fg': 160, 'codes': 1},
    logging.FATAL: {'fg': 226, 'bg': 52, 'codes': 1},
}

palette_map = {
    'sensible': _sensible,
    'sensible_light': _sensible_light,
    'forest': _forest,
    'synth': _synth,
    'ocean': _ocean,
    'dawn': _dawn,
}


class Palette:
    """Contains the settings for text formatting and colour based on log level.

    This class can be initialised from a preset colour palette by name, or
    given a custom dictionary (see the ones in the timbermafia.palettes module
    for details).

    The recommended way to change colours and formatting for each log level is
    to use the method set_level.

    Args:
        preset: Name of a preset palette from which to configure (call
            timbermafia.print_palettes() to see presets).
        custom: A dict containing the settings, should look like:
            {
                logging.INFO: {'fg': 200, 'bg': 100, 'codes': 1},
                logging.WARNING: {'fg': 140, 'codes': [5, 1] },
            }
    """

    def __init__(self, preset=None, custom=None):
        """Init from either a preset palette, or a custom palette dict.

        Palettes generated from presets can be easily changed in-place
        and are recommended.

        If custom palettes are provided they should resemble the dicts
        for the palettes present in this module.
        """
        self.palette_dict = {}

        # If given a preset get those settings.
        self.palette_dict = palette_map[preset]

        # If given a colour map directly, use it.
        if custom:
            try:
                self.palette_dict.update(custom)
            except ValueError:
                raise

    ############################################################
    # Summarise the current state of the palette.
    ############################################################
    def summarise(self):
        """Print sample colour outputs for each level."""
        for level, name in logging._levelToName.items():
            s = utils.RESET + self.get_ansi_string(level) +\
                f'{name} looks like this' + utils.RESET
            print(s)

    ############################################################
    # Properties and functions to configure the palette.
    ############################################################
    def update_colours(self, custom):
        """Update the existing palette settings from a custom palette dict.

        If a given level's settings are not specified it is unaltered.
        """
        for key in custom:
            if key in self.palette_dict:
                self.palette_dict[key].update(custom[key])
            else:
                self.palette_dict[key] = custom[key]

    def set_colours(self, custom):
        """Overwrite existing palette settings from a custom palette dict."""
        self.palette_dict = custom

    def set_level(self, level, fg=None, bg=None, codes=None, overwrite=False):
        """Set a given level's colour and appearance settings.

        Args:
            level: The integer corresponding to the requested level, e.g.
                20, logging.DEBUG etc.
            fg: The 8-bit foreground ANSI colour code for this level.
            bg: The 8-bit background ANSI colour code for this level.
            codes: An iterable of integers indicating ANSI flags to use.
            overwrite: If True, overwrites any existing config for this level.
        """
        d = {}
        if fg:
            d['fg'] = fg
        if bg:
            d['bg'] = bg
        if codes:
            d['codes'] = codes
        if overwrite:
            self.palette_dict[level] = d
        else:
            self.palette_dict[level].update(d)

    ############################################################
    # Funcs for use by the timbermafia classes.
    ############################################################
    @staticmethod
    def get_fg_ansi(code):
        return '\033[38;5;' + str(code) + 'm'

    @staticmethod
    def get_bg_ansi(code):
        return '\033[48;5;' + str(code) + 'm'

    @staticmethod
    def get_other_ansi_codes(codes):
        s = ''
        if isinstance(codes, int):
            s += '\033[' + str(codes) + 'm'
        elif isinstance(codes, collections.abc.Iterable):
            for c in codes:
                s += '\033[' + str(c) + 'm'
        return s

    def get_ansi_string(self, levelno):
        s = ''
        d = self.palette_dict.get(levelno)
        if not d:
            return s
        fg = d.get('fg')
        if fg:
            s += self.get_fg_ansi(fg)
        bg = d.get('bg')
        if bg:
            s += self.get_bg_ansi(bg)
        codes = d.get('codes')
        if codes:
            s += self.get_other_ansi_codes(codes)
        return s

    def get_colourised_lines(self, levelno, lines):
        ansi = self.get_ansi_string(levelno)
        new_lines = []
        for line in lines:

            # Add the colour at the start of the line
            line = ansi + line

            # Now find any resets and replace them with a
            # reset + our new ansi.
            line = line.replace(utils.RESET, utils.RESET+ansi)

            # Add a final reset
            line = line + utils.RESET
            new_lines.append(line)

        return new_lines
