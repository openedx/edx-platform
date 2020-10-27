from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.program_enrollments')

from lms.djangoapps.support.views.program_enrollments import *
