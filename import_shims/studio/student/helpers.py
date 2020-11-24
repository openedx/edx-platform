from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.helpers', 'common.djangoapps.student.helpers')

from common.djangoapps.student.helpers import *
