from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_api', 'lms.djangoapps.instructor.tests.test_api')

from lms.djangoapps.instructor.tests.test_api import *
