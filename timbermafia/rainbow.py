import logging
from timbermafia.utils import LOCALFILE, URL


fg = "\033[38;5;{}m"
bg = "\033[48;5;{}m"
# reset = "\033[39m"
reset = "\033[0m"

# Preset colour palettes using 8-bit ANSI codes.
sensible = {
    logging.DEBUG: (33, None, False),
    logging.INFO: (255, None, False),
    logging.WARNING: (214, None, False),
    logging.ERROR: (196, None, True),
    logging.FATAL: (40, 52, True),
    LOCALFILE: (184, None, True),
    URL: (44, None, True),
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

palette_dict = {
    'sensible': sensible,
    'sensible_light': sensible_light,
    'forest': forest,
    'synth': synth,
    'ocean': ocean,
    'dawn': dawn,
}


class RainbowStreamHandler(logging.StreamHandler):
    """
    Stream handler with support for automatic colouring of text
    depending on log levels, filepaths, URLs etc.

    Taken extensively from Will Breaden-Madden's technicolor package.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        config = kwargs.get('config')
        colour_map_key = config['palette']
        self.config = config
        self.level_map = palette_dict.get(colour_map_key)

    def istty(self):
        isatty = getattr(self.stream, "isatty", None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.istty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, "terminator", "\n"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def output_colorized(self, message):
        self.stream.write(message)

    def colorize(self, message, record):
        levelno = None
        # print(record, isinstance(record, str))
        if isinstance(record, str):
            levelno = record
        else:
            levelno = record.levelno
        if levelno in self.level_map:
            fg_color, bg_color, bold = self.level_map[levelno]
            parameters = []
            if bold:
                if self.config['bold']:
                    parameters.append('\033[1m')
            if bg_color:
                parameters.append(bg.format(bg_color))
            if fg_color:
                parameters.append(fg.format(fg_color))
            if parameters:
                message = "".join(
                    ("".join(parameters), message, reset)
                )
        return message

    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        if self.istty:

            # Colour all multi-line output.
            parts = message.split("\n", 1)
            for index, part in enumerate(parts):
                parts[index] = self.colorize(part, record)
            message = "\n".join(parts)

            # File and URLs
            parts = message.split(' ')
            for index, part in enumerate(parts):
                if not part:
                    continue
                if part[0] == '/':
                    parts[index] = self.colorize(part, 'file')
                elif part.startswith('http') or part.startswith('www'):
                    parts[index] = self.colorize(part, 'url')
            message = " ".join(parts)
        return message