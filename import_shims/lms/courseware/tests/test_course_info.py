from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_course_info', 'lms.djangoapps.courseware.tests.test_course_info')

from lms.djangoapps.courseware.tests.test_course_info import *
