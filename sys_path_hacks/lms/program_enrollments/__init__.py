import warnings
warnings.warn("Importing program_enrollments instead of lms.djangoapps.program_enrollments is deprecated", stacklevel=2)

from lms.djangoapps.program_enrollments import *
