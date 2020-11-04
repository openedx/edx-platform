from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.auth', 'common.djangoapps.student.auth')

from common.djangoapps.student.auth import *
