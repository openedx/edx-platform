from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.message_types', 'common.djangoapps.student.message_types')

from common.djangoapps.student.message_types import *
