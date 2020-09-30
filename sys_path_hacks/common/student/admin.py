from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.admin')

from common.djangoapps.student.admin import *
