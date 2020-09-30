from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.middleware')

from common.djangoapps.student.middleware import *
