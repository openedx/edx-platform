from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.tracker')

from common.djangoapps.track.tracker import *
