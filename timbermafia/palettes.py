import logging
import sys
import timbermafia.utils as utils
from timbermafia.utils import LOCALFILE, URL, RESET

# Preset colour palettes using 8-bit ANSI codes.
sensible = {
    logging.DEBUG: (33, None, False),
    logging.INFO: (255, None, False),
    logging.WARNING: (214, None, False),
    logging.ERROR: (196, None, True),
    logging.FATAL: (40, 52, True),
    LOCALFILE: (154, None, True),
    URL: (44, None, True),
}

sensible2 = {
    logging.DEBUG: {'fg': 33},
    logging.INFO: {'fg', 255},
    logging.WARNING: {'fg': 214},
    logging.ERROR: {'fg': 196, 'codes': '1'},
    logging.FATAL: {'fg': 40, 'bg': 52, 'codes': '1'},
}

sensible_light = {
    logging.DEBUG: (18, None, False),
    logging.INFO: (232, None, False),
    logging.WARNING: (130, None, False),
    logging.ERROR: (196, None, True),
    logging.FATAL: (40, 52, True),
    LOCALFILE: (165, None, True),
    URL: (44, None, True),
}

forest = {
    logging.DEBUG: (22, None, False),
    logging.INFO: (34, None, False),
    logging.WARNING: (202, None, False),
    logging.ERROR: (94, None, True),
    logging.FATAL: (0, 94, True),
    LOCALFILE: (12, None, True),
    URL: (31, None, True),
}

ocean = {
    logging.DEBUG: (27, None, False),
    logging.INFO: (45, None, False),
    logging.WARNING: (47, None, False),
    logging.ERROR: (226, None, True),
    logging.FATAL: (226, 18, True),
    LOCALFILE: (7, None, True),
    URL: (7, None, True),
}

synth = {
    logging.DEBUG: (51, None, False),
    logging.INFO: (201, None, False),
    logging.WARNING: (225, None, False),
    logging.ERROR: (213, None, True),
    logging.FATAL: (44, 57, True),
    LOCALFILE: (7, None, True),
    URL: (63, None, True),
}

dawn = {
    logging.DEBUG: (200, None, False),
    logging.INFO: (208, None, False),
    logging.WARNING: (190, None, False),
    logging.ERROR: (160, None, True),
    logging.FATAL: (226, 52, True),
    LOCALFILE: (7, None, True),
    URL: (147, None, True),
}

PALETTE_DICT = {
    'sensible': sensible,
    'sensible2': sensible2,
    'sensible_light': sensible_light,
    'forest': forest,
    'synth': synth,
    'ocean': ocean,
    'dawn': dawn,
}


class Palette:
    """
    Class to hold the colour settings, and to colourise input based on
    a LogRecord level.
    """

    def __init__(self, preset=None, custom=None):
        self.palette_dict = {}

        # If given a preset get those settings.
        if preset:
            try:
                self.palette_dict.update(PALETTE_DICT[preset])
            except KeyError:
                raise

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
        print(d)
        if not d:
            return s

        fg = d.get('fg')
        if fg:
            s += '\033[38;5;' + fg + 'm'
        bg = d.get('bg')
        if bg:
            s += '\033[48;5;' + bg + 'm'
        codes_string = d.get('codes')
        if codes_string:
            codes = codes_string.split(',')
            for c in codes:
                s += '\033[' + c + 'm'
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
