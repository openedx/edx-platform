from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.api', 'common.djangoapps.student.api')

from common.djangoapps.student.api import *
