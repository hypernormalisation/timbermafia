import timbermafia as tm

tm.print_styles()
tm.print_palettes()

# s = tm.generate_default_style()
# s.summarise()
#
# s.format = '{asctime:u} _ {levelname} _ {message}'
# s.datefmt = '%m/%d/%Y %H:%M:%S'
# s.max_width = 180
# s.width = 140
# s.short_levels = True
# s.set_justification('name', 'l')
# # s.colourised_levels = False
#
# s.summarise()
#
# tm.basic_config(style=s)
#
# import logging
# log = logging.getLogger(__name__)
# log.debug('Here is some debug info')
# log.warning('Here is some warning info, something here needs more inspection')