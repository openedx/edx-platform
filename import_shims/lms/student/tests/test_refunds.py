from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_refunds', 'common.djangoapps.student.tests.test_refunds')

from common.djangoapps.student.tests.test_refunds import *
