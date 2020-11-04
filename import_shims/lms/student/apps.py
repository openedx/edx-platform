from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.apps', 'common.djangoapps.student.apps')

from common.djangoapps.student.apps import *
