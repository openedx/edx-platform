from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.course_grade', 'lms.djangoapps.grades.course_grade')

from lms.djangoapps.grades.course_grade import *
