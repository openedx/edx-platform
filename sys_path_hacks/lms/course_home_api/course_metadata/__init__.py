import warnings
warnings.warn("Importing course_home_api.course_metadata instead of lms.djangoapps.course_home_api.course_metadata is deprecated", stacklevel=2)

from lms.djangoapps.course_home_api.course_metadata import *
