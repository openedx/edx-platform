import warnings
warnings.warn("Importing course_api.forms instead of lms.djangoapps.course_api.forms is deprecated", stacklevel=2)

from lms.djangoapps.course_api.forms import *
