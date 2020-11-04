from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.tests.test_manage_group', 'common.djangoapps.student.management.tests.test_manage_group')

from common.djangoapps.student.management.tests.test_manage_group import *
