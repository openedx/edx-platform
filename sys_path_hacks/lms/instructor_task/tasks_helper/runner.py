import warnings
warnings.warn("Importing instructor_task.tasks_helper.runner instead of lms.djangoapps.instructor_task.tasks_helper.runner is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.tasks_helper.runner import *
