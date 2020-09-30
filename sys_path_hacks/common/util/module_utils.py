from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.module_utils')

from common.djangoapps.util.module_utils import *
