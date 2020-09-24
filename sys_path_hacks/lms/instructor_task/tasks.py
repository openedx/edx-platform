import warnings
warnings.warn("Importing instructor_task.tasks instead of lms.djangoapps.instructor_task.tasks is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.tasks import *
