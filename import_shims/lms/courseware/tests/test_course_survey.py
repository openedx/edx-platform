from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.tests.test_course_survey', 'lms.djangoapps.courseware.tests.test_course_survey')

from lms.djangoapps.courseware.tests.test_course_survey import *
