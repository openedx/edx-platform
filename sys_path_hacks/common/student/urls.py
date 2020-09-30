from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.urls')

from common.djangoapps.student.urls import *
