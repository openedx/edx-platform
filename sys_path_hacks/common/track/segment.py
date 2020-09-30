from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.segment')

from common.djangoapps.track.segment import *
