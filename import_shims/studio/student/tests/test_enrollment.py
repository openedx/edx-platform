from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_enrollment', 'common.djangoapps.student.tests.test_enrollment')

from common.djangoapps.student.tests.test_enrollment import *
