from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_views', 'common.djangoapps.student.tests.test_views')

from common.djangoapps.student.tests.test_views import *
