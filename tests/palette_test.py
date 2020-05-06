import logging
from timbermafia.palettes import Palette

my_colours = {
    logging.DEBUG: {'fg': 200}
}

p = Palette(preset='sensible2')
print(p.palette_dict)

p.update_colours(my_colours)
print(p.palette_dict)

p.set_colour(logging.ERROR, fg='145')
print(p.palette_dict)

print(p.get_ansi_string(logging.ERROR).encode('unicode-escape'))
