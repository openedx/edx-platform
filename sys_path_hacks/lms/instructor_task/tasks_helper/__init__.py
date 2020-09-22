import warnings
warnings.warn("Importing instructor_task.tasks_helper instead of lms.djangoapps.instructor_task.tasks_helper is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.tasks_helper import *
