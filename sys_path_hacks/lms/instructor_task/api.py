import warnings
warnings.warn("Importing instructor_task.api instead of lms.djangoapps.instructor_task.api is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.api import *
