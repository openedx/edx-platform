from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.util_services', 'lms.djangoapps.grades.util_services')

from lms.djangoapps.grades.util_services import *
