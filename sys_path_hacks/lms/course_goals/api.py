import warnings
warnings.warn("Importing course_goals.api instead of lms.djangoapps.course_goals.api is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.api import *
