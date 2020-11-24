from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.apps', 'common.djangoapps.course_modes.apps')

from common.djangoapps.course_modes.apps import *
