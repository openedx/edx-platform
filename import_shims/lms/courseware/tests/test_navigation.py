from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_navigation', 'lms.djangoapps.courseware.tests.test_navigation')

from lms.djangoapps.courseware.tests.test_navigation import *
