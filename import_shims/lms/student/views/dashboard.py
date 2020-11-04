from import_shims.warn import warn_deprecated_import

warn_deprecated_import('student.views.dashboard', 'common.djangoapps.student.views.dashboard')

from common.djangoapps.student.views.dashboard import *
