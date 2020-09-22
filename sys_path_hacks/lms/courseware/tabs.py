import warnings
warnings.warn("Importing courseware.tabs instead of lms.djangoapps.courseware.tabs is deprecated", stacklevel=2)

from lms.djangoapps.courseware.tabs import *
