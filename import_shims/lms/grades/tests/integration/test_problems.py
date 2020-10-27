from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.integration.test_problems', 'lms.djangoapps.grades.tests.integration.test_problems')

from lms.djangoapps.grades.tests.integration.test_problems import *
