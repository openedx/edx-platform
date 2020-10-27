from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_email', 'lms.djangoapps.instructor.tests.test_email')

from lms.djangoapps.instructor.tests.test_email import *
