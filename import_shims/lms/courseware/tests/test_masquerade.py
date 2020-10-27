from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_masquerade', 'lms.djangoapps.courseware.tests.test_masquerade')

from lms.djangoapps.courseware.tests.test_masquerade import *
