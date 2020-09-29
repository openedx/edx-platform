from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.enrollment')

from lms.djangoapps.instructor.enrollment import *
