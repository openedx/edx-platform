from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.management.tracked_command')

from common.djangoapps.track.management.tracked_command import *
