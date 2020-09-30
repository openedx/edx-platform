from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.management.commands.tracked_dummy_command')

from common.djangoapps.track.management.commands.tracked_dummy_command import *
