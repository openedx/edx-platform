from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'database_fixups')

from common.djangoapps.database_fixups import *
