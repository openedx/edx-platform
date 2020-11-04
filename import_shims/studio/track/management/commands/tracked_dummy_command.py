from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.management.commands.tracked_dummy_command', 'common.djangoapps.track.management.commands.tracked_dummy_command')

from common.djangoapps.track.management.commands.tracked_dummy_command import *
