from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests.test_course', 'common.djangoapps.util.tests.test_course')

from common.djangoapps.util.tests.test_course import *
