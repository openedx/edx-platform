from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.config', 'lms.djangoapps.grades.config')

from lms.djangoapps.grades.config import *
