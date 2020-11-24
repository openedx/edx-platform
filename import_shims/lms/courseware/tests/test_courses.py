from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_courses', 'lms.djangoapps.courseware.tests.test_courses')

from lms.djangoapps.courseware.tests.test_courses import *
