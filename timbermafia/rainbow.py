import logging

fg = "\033[38;5;{}m"
bg = "\033[48;5;{}m"
reset = "\033[39m"


# Preset colour palettes
neon = {
    logging.DEBUG: (44, None),
    logging.INFO: (15, None),
    logging.WARNING: (214, None),
    logging.ERROR: (196, None),
    logging.FATAL: (196, None),
    'file': (184, None),
    'url': (201, None),
}

palette_dict = {
    'neon': neon,
}


class RainbowStreamHandler(logging.StreamHandler):
    """
    Stream handler with support for automatic colouring of text
    depending on log levels, filepaths, URLs etc.

    Taken extensively from Will Breaden-Madden's technicolor package.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        colour_map_key = kwargs.get('palette')
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
            fg_color, bg_color = self.level_map[levelno]
            parameters = []
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