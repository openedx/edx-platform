from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.tests.test_forms', 'lms.djangoapps.course_api.tests.test_forms')

from lms.djangoapps.course_api.tests.test_forms import *
