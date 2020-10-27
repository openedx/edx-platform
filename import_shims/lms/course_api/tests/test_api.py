from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.tests.test_api', 'lms.djangoapps.course_api.tests.test_api')

from lms.djangoapps.course_api.tests.test_api import *
