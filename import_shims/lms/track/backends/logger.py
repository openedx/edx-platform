from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.backends.logger', 'common.djangoapps.track.backends.logger')

from common.djangoapps.track.backends.logger import *
