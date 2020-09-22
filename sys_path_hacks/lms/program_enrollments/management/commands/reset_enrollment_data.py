import warnings
warnings.warn("Importing program_enrollments.management.commands.reset_enrollment_data instead of lms.djangoapps.program_enrollments.management.commands.reset_enrollment_data is deprecated", stacklevel=2)

from lms.djangoapps.program_enrollments.management.commands.reset_enrollment_data import *
