from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_models', 'lms.djangoapps.grades.tests.test_models')

from lms.djangoapps.grades.tests.test_models import *
