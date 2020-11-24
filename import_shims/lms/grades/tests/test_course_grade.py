from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_course_grade', 'lms.djangoapps.grades.tests.test_course_grade')

from lms.djangoapps.grades.tests.test_course_grade import *
