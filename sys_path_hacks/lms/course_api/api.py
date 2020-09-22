import warnings
warnings.warn("Importing course_api.api instead of lms.djangoapps.course_api.api is deprecated", stacklevel=2)

from lms.djangoapps.course_api.api import *
