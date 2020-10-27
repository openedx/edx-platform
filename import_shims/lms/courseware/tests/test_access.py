from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_access', 'lms.djangoapps.courseware.tests.test_access')

from lms.djangoapps.courseware.tests.test_access import *
