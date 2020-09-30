from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track')

from common.djangoapps.track import *
