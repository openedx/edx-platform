import warnings
warnings.warn("Importing course_goals.handlers instead of lms.djangoapps.course_goals.handlers is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.handlers import *
