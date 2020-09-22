import warnings
warnings.warn("Importing program_enrollments.management.commands.expire_waiting_enrollments instead of lms.djangoapps.program_enrollments.management.commands.expire_waiting_enrollments is deprecated", stacklevel=2)

from lms.djangoapps.program_enrollments.management.commands.expire_waiting_enrollments import *
