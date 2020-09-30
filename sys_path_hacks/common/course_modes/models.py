from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'course_modes.models')

from common.djangoapps.course_modes.models import *
