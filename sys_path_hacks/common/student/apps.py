from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.apps')

from common.djangoapps.student.apps import *
