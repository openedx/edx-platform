from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.validate_on_save')

from common.djangoapps.util.validate_on_save import *
