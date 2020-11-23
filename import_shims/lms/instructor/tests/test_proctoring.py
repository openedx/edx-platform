from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_proctoring', 'lms.djangoapps.instructor.tests.test_proctoring')

from lms.djangoapps.instructor.tests.test_proctoring import *
