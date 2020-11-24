from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.management.commands', 'common.djangoapps.track.management.commands')

from common.djangoapps.track.management.commands import *
