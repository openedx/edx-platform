from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.request_rate_limiter')

from common.djangoapps.util.request_rate_limiter import *
