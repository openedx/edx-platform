from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.signals', 'common.djangoapps.student.signals')

from common.djangoapps.student.signals import *
