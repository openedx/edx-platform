from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.api', 'common.djangoapps.course_modes.api')

from common.djangoapps.course_modes.api import *
