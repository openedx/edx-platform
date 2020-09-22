import warnings
warnings.warn("Importing courseware.admin instead of lms.djangoapps.courseware.admin is deprecated", stacklevel=2)

from lms.djangoapps.courseware.admin import *
