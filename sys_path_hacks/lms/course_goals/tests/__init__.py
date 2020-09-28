import warnings
warnings.warn("Importing course_goals.tests instead of lms.djangoapps.course_goals.tests is deprecated", stacklevel=2)

from lms.djangoapps.course_goals.tests import *
