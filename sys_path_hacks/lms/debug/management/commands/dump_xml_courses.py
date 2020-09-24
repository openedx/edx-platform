import warnings
warnings.warn("Importing debug.management.commands.dump_xml_courses instead of lms.djangoapps.debug.management.commands.dump_xml_courses is deprecated", stacklevel=2)

from lms.djangoapps.debug.management.commands.dump_xml_courses import *
