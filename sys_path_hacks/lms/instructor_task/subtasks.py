import warnings
warnings.warn("Importing instructor_task.subtasks instead of lms.djangoapps.instructor_task.subtasks is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.subtasks import *
