from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_course_tools', 'lms.djangoapps.courseware.tests.test_course_tools')

from lms.djangoapps.courseware.tests.test_course_tools import *
