from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.urls')

from common.djangoapps.track.urls import *
