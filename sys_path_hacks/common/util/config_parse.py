from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.config_parse')

from common.djangoapps.util.config_parse import *
