import warnings
warnings.warn("Importing instructor_task.management.commands instead of lms.djangoapps.instructor_task.management.commands is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.management.commands import *
