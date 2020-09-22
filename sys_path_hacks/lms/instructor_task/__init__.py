import warnings
warnings.warn("Importing instructor_task instead of lms.djangoapps.instructor_task is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task import *
