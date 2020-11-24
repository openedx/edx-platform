from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.cache', 'common.djangoapps.util.cache')

from common.djangoapps.util.cache import *
