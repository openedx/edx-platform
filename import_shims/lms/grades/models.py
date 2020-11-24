from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.models', 'lms.djangoapps.grades.models')

from lms.djangoapps.grades.models import *
