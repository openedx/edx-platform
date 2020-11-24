from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_credit', 'common.djangoapps.student.tests.test_credit')

from common.djangoapps.student.tests.test_credit import *
