from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.course_grade_factory', 'lms.djangoapps.grades.course_grade_factory')

from lms.djangoapps.grades.course_grade_factory import *
