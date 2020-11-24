from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_password_policy', 'common.djangoapps.student.tests.test_password_policy')

from common.djangoapps.student.tests.test_password_policy import *
