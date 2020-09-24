import warnings
warnings.warn("Importing courseware.management.commands instead of lms.djangoapps.courseware.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.courseware.management.commands import *
