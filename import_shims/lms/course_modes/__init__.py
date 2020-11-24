from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes', 'common.djangoapps.course_modes')

from common.djangoapps.course_modes import *
