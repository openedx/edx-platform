from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.grade_utils', 'lms.djangoapps.grades.grade_utils')

from lms.djangoapps.grades.grade_utils import *
