from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.request_rate_limiter', 'common.djangoapps.util.request_rate_limiter')

from common.djangoapps.util.request_rate_limiter import *
