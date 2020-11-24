from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student', 'common.djangoapps.student')

from common.djangoapps.student import *
