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

palette_dict = {
    'sensible': _sensible,
    'sensible_light': _sensible_light,
    'forest': _forest,
    'synth': _synth,
    'ocean': _ocean,
    'dawn': _dawn,
}


class Palette:
    """
    Class to hold the colour settings, and to colourise input based on
    a LogRecord level.
    """

    def __init__(self, preset=None, custom=None):
        self.palette_dict = {}

        # If given a preset get those settings.
        self.palette_dict = palette_dict[preset]

        # If given a colour map directly, use it.
        if custom:
            try:
                self.palette_dict.update(custom)
            except ValueError:
                raise

    def update_colours(self, custom):
        for key in custom:
            if key in self.palette_dict:
                self.palette_dict[key].update(custom[key])
            else:
                self.palette_dict[key] = custom[key]

    def set_colours(self, custom):
        self.palette_dict = custom

    def set_colour(self, levelno, **kwargs):
        d = {}
        for kw in kwargs:
            d[kw] = kwargs[kw]
        self.palette_dict[levelno] = d

    def get_ansi_string(self, levelno):
        s = ''
        d = self.palette_dict.get(levelno)
        if not d:
            return s

        fg = d.get('fg')
        if fg:
            s += '\033[38;5;' + str(fg) + 'm'
        bg = d.get('bg')
        if bg:
            s += '\033[48;5;' + str(bg) + 'm'
        codes = d.get('codes')
        if isinstance(codes, int):
            s += '\033[' + str(codes) + 'm'
        elif isinstance(codes, collections.abc.Iterable):
            for c in codes:
                s += '\033[' + str(c) + 'm'
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
