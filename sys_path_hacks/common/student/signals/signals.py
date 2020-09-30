from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.signals.signals')

from common.djangoapps.student.signals.signals import *
