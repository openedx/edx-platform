from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_certificates', 'lms.djangoapps.instructor.tests.test_certificates')

from lms.djangoapps.instructor.tests.test_certificates import *
