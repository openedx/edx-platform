import warnings
warnings.warn("Importing courseware instead of lms.djangoapps.courseware is deprecated", stacklevel=2)

from lms.djangoapps.courseware import *
