from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'course_modes.tests.test_signals')

from common.djangoapps.course_modes.tests.test_signals import *
