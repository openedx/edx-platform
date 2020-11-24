from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_tabs', 'lms.djangoapps.courseware.tests.test_tabs')

from lms.djangoapps.courseware.tests.test_tabs import *
