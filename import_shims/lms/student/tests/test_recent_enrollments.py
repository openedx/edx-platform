from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_recent_enrollments', 'common.djangoapps.student.tests.test_recent_enrollments')

from common.djangoapps.student.tests.test_recent_enrollments import *
