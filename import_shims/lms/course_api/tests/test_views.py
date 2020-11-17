from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.tests.test_views', 'lms.djangoapps.course_api.tests.test_views')

from lms.djangoapps.course_api.tests.test_views import *
