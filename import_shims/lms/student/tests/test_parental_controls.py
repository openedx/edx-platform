from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_parental_controls', 'common.djangoapps.student.tests.test_parental_controls')

from common.djangoapps.student.tests.test_parental_controls import *
