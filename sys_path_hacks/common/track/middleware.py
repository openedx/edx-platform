from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.middleware')

from common.djangoapps.track.middleware import *
