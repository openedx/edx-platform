from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.tests.test_user_profile_properties')

from common.djangoapps.student.tests.test_user_profile_properties import *
