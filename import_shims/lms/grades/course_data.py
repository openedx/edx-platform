from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.course_data', 'lms.djangoapps.grades.course_data')

from lms.djangoapps.grades.course_data import *
