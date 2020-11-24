from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.backends', 'common.djangoapps.track.backends')

from common.djangoapps.track.backends import *
