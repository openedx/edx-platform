from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.permissions')

from lms.djangoapps.instructor.permissions import *
