from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.exceptions', 'lms.djangoapps.grades.exceptions')

from lms.djangoapps.grades.exceptions import *
