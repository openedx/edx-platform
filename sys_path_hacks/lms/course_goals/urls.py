import warnings
warnings.warn("Importing course_goals.urls instead of lms.djangoapps.course_goals.urls is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.urls import *
