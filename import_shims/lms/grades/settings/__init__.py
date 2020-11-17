from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.settings', 'lms.djangoapps.grades.settings')

from lms.djangoapps.grades.settings import *
