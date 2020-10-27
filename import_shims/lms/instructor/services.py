from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.services')

from lms.djangoapps.instructor.services import *
