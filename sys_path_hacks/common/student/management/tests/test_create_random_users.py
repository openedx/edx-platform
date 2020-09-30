from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.tests.test_create_random_users')

from common.djangoapps.student.management.tests.test_create_random_users import *
