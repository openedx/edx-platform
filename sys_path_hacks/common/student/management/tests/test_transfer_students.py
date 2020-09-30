from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.tests.test_transfer_students')

from common.djangoapps.student.management.tests.test_transfer_students import *
