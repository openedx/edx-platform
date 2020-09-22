import warnings
warnings.warn("Importing course_api.permissions instead of lms.djangoapps.course_api.permissions is deprecated", stacklevel=2)

from lms.djangoapps.course_api.permissions import *
