from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.disable_rate_limit', 'common.djangoapps.util.disable_rate_limit')

from common.djangoapps.util.disable_rate_limit import *
