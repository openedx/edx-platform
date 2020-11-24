from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_signals', 'lms.djangoapps.grades.tests.test_signals')

from lms.djangoapps.grades.tests.test_signals import *
