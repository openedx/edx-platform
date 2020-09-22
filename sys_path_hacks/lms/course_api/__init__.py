import warnings
warnings.warn("Importing course_api instead of lms.djangoapps.course_api is deprecated", stacklevel=2)

from lms.djangoapps.course_api import *
