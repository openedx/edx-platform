from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_footer', 'lms.djangoapps.courseware.tests.test_footer')

from lms.djangoapps.courseware.tests.test_footer import *
