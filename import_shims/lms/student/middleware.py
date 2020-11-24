from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.middleware', 'common.djangoapps.student.middleware')

from common.djangoapps.student.middleware import *
