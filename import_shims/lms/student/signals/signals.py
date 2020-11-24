from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.signals.signals', 'common.djangoapps.student.signals.signals')

from common.djangoapps.student.signals.signals import *
