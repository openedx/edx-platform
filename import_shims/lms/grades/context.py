from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.context', 'lms.djangoapps.grades.context')

from lms.djangoapps.grades.context import *
