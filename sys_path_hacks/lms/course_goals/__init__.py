import warnings
warnings.warn("Importing course_goals instead of lms.djangoapps.course_goals is deprecated", stacklevel=2)

from lms.djangoapps.course_goals import *
