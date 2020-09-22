import warnings
warnings.warn("Importing program_enrollments.tasks instead of lms.djangoapps.program_enrollments.tasks is deprecated", stacklevel=2)

from lms.djangoapps.program_enrollments.tasks import *
