from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_scores', 'lms.djangoapps.grades.tests.test_scores')

from lms.djangoapps.grades.tests.test_scores import *
