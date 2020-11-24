from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.urls', 'common.djangoapps.track.urls')

from common.djangoapps.track.urls import *
