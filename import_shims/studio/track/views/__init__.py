from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.views', 'common.djangoapps.track.views')

from common.djangoapps.track.views import *
