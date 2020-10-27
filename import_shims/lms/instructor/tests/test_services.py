from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_services', 'lms.djangoapps.instructor.tests.test_services')

from lms.djangoapps.instructor.tests.test_services import *
