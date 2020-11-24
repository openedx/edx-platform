from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.tracker', 'common.djangoapps.track.tracker')

from common.djangoapps.track.tracker import *
