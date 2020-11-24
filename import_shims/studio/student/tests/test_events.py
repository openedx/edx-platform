from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_events', 'common.djangoapps.student.tests.test_events')

from common.djangoapps.student.tests.test_events import *
