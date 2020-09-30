from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'course_modes.views')

from common.djangoapps.course_modes.views import *
