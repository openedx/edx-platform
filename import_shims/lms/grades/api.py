from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.api', 'lms.djangoapps.grades.api')

from lms.djangoapps.grades.api import *
