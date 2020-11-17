from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor.tests.test_tools', 'lms.djangoapps.instructor.tests.test_tools')

from lms.djangoapps.instructor.tests.test_tools import *
