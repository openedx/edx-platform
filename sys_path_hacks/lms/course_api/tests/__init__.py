import warnings
warnings.warn("Importing course_api.tests instead of lms.djangoapps.course_api.tests is deprecated", stacklevel=2)

from lms.djangoapps.course_api.tests import *
