from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.views', 'common.djangoapps.student.views')

from common.djangoapps.student.views import *
