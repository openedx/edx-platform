import warnings
warnings.warn("Importing course_api.views instead of lms.djangoapps.course_api.views is deprecated", stacklevel=2)

from lms.djangoapps.course_api.views import *
