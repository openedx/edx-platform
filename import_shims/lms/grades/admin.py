from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.admin', 'lms.djangoapps.grades.admin')

from lms.djangoapps.grades.admin import *
