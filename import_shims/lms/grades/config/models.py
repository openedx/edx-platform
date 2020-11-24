from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.config.models', 'lms.djangoapps.grades.config.models')

from lms.djangoapps.grades.config.models import *
