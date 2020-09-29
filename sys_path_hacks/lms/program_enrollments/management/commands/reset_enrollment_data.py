from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'program_enrollments.management.commands.reset_enrollment_data')

from lms.djangoapps.program_enrollments.management.commands.reset_enrollment_data import *
