from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.models', 'common.djangoapps.course_modes.models')

from common.djangoapps.course_modes.models import *
