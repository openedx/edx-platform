from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_email', 'common.djangoapps.student.tests.test_email')

from common.djangoapps.student.tests.test_email import *
