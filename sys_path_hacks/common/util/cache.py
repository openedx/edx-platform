from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.cache')

from common.djangoapps.util.cache import *
