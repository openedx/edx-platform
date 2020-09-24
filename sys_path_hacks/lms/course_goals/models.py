import warnings
warnings.warn("Importing course_goals.models instead of lms.djangoapps.course_goals.models is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.models import *
