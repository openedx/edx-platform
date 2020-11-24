from import_shims.warn import warn_deprecated_import

warn_deprecated_import('debug.views', 'lms.djangoapps.debug.views')

from lms.djangoapps.debug.views import *
