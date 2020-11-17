from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_api', 'lms.djangoapps.grades.tests.test_api')

from lms.djangoapps.grades.tests.test_api import *
