from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.signals.receivers', 'common.djangoapps.student.signals.receivers')

from common.djangoapps.student.signals.receivers import *
