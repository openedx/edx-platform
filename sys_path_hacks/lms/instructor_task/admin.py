import warnings
warnings.warn("Importing instructor_task.admin instead of lms.djangoapps.instructor_task.admin is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.admin import *
