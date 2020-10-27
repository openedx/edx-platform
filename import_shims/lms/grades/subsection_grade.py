from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.subsection_grade')

from lms.djangoapps.grades.subsection_grade import *
