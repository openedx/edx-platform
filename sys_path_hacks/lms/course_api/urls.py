import warnings
warnings.warn("Importing course_api.urls instead of lms.djangoapps.course_api.urls is deprecated", stacklevel=2)

from lms.djangoapps.course_api.urls import *
