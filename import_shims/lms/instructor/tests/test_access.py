from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_access', 'lms.djangoapps.instructor.tests.test_access')

from lms.djangoapps.instructor.tests.test_access import *
