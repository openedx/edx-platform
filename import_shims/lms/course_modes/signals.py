from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.signals', 'common.djangoapps.course_modes.signals')

from common.djangoapps.course_modes.signals import *
