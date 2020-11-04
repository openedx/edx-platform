from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.admin', 'common.djangoapps.course_modes.admin')

from common.djangoapps.course_modes.admin import *
