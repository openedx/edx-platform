from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.role_helpers')

from common.djangoapps.student.role_helpers import *
