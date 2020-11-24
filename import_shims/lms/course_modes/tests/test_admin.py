from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_modes.tests.test_admin', 'common.djangoapps.course_modes.tests.test_admin')

from common.djangoapps.course_modes.tests.test_admin import *
