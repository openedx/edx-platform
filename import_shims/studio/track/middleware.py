from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.middleware', 'common.djangoapps.track.middleware')

from common.djangoapps.track.middleware import *
