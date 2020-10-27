from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.utils')

from lms.djangoapps.instructor.utils import *
