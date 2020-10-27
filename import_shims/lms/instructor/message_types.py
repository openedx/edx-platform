from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.message_types')

from lms.djangoapps.instructor.message_types import *
