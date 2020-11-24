from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.management.tests.test_manage_user', 'common.djangoapps.student.management.tests.test_manage_user')

from common.djangoapps.student.management.tests.test_manage_user import *
