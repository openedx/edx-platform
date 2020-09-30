from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.disable_rate_limit')

from common.djangoapps.util.disable_rate_limit import *
