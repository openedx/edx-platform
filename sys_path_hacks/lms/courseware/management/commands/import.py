import warnings
warnings.warn("Importing courseware.management.commands.import instead of lms.djangoapps.courseware.management.commands.import is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands.import import *
