import warnings
warnings.warn("Importing course_home_api instead of lms.djangoapps.course_home_api is deprecated", stacklevel=2)

from lms.djangoapps.course_home_api import *
