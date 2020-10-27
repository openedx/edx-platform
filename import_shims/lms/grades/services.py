from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.services', 'lms.djangoapps.grades.services')

from lms.djangoapps.grades.services import *
