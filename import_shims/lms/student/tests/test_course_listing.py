from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.tests.test_course_listing', 'common.djangoapps.student.tests.test_course_listing')

from common.djangoapps.student.tests.test_course_listing import *
