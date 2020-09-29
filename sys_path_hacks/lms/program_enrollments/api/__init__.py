from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'program_enrollments.api')

from lms.djangoapps.program_enrollments.api import *
