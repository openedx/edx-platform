from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.subsection_grade', 'lms.djangoapps.grades.subsection_grade')

from lms.djangoapps.grades.subsection_grade import *
