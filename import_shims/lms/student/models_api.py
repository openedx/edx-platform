from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.models_api', 'common.djangoapps.student.models_api')

from common.djangoapps.student.models_api import *
