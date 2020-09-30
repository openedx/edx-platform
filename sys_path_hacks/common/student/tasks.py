from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.tasks')

from common.djangoapps.student.tasks import *
