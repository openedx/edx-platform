import warnings
warnings.warn("Importing courseware.rules instead of lms.djangoapps.courseware.rules is deprecated", stacklevel=2)

from lms.djangoapps.courseware.rules import *
