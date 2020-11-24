from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_course_data', 'lms.djangoapps.grades.tests.test_course_data')

from lms.djangoapps.grades.tests.test_course_data import *
