from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'course_modes.tests.test_views')

from common.djangoapps.course_modes.tests.test_views import *
