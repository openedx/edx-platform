from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.auth')

from common.djangoapps.student.auth import *
