from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.admin', 'common.djangoapps.student.admin')

from common.djangoapps.student.admin import *
