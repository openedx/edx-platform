from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.forms')

from common.djangoapps.student.forms import *
