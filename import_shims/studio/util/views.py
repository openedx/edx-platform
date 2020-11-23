from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.views', 'common.djangoapps.util.views')

from common.djangoapps.util.views import *
