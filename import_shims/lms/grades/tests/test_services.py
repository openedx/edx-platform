from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_services', 'lms.djangoapps.grades.tests.test_services')

from lms.djangoapps.grades.tests.test_services import *
