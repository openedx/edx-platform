from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.tests.test_manage_group')

from common.djangoapps.student.management.tests.test_manage_group import *
