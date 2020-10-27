from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.course_grade')

from lms.djangoapps.grades.course_grade import *
