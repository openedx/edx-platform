from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.models_api', 'lms.djangoapps.grades.models_api')

from lms.djangoapps.grades.models_api import *
