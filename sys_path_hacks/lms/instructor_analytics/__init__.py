import warnings
warnings.warn("Importing instructor_analytics instead of lms.djangoapps.instructor_analytics is deprecated", stacklevel=2)

from lms.djangoapps.instructor_analytics import *
