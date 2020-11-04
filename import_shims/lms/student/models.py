from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.models', 'common.djangoapps.student.models')

from common.djangoapps.student.models import *
