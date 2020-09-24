import warnings
warnings.warn("Importing course_goals.apps instead of lms.djangoapps.course_goals.apps is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.apps import *
