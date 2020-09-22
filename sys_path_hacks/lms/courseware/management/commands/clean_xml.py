import warnings
warnings.warn("Importing courseware.management.commands.clean_xml instead of lms.djangoapps.courseware.management.commands.clean_xml is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands.clean_xml import *
