from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_userstanding', 'common.djangoapps.student.tests.test_userstanding')

from common.djangoapps.student.tests.test_userstanding import *
