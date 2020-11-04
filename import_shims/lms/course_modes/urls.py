from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.urls', 'common.djangoapps.course_modes.urls')

from common.djangoapps.course_modes.urls import *
