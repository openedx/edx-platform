from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.backends.mongodb')

from common.djangoapps.track.backends.mongodb import *
