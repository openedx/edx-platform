import warnings
warnings.warn("Importing instructor_task.management instead of lms.djangoapps.instructor_task.management is deprecated", stacklevel=2)

from lms.djangoapps.instructor_task.management import *
