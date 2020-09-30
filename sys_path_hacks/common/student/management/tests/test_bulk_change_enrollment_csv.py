from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.management.tests.test_bulk_change_enrollment_csv')

from common.djangoapps.student.management.tests.test_bulk_change_enrollment_csv import *
