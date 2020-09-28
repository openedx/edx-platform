import warnings
warnings.warn("Importing instructor_task.tasks_base instead of lms.djangoapps.instructor_task.tasks_base is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.tasks_base import *
