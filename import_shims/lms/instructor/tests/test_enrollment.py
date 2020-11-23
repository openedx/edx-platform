from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_enrollment', 'lms.djangoapps.instructor.tests.test_enrollment')

from lms.djangoapps.instructor.tests.test_enrollment import *
