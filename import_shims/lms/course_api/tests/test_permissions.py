from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.tests.test_permissions', 'lms.djangoapps.course_api.tests.test_permissions')

from lms.djangoapps.course_api.tests.test_permissions import *
