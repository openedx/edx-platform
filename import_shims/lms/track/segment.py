from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.segment', 'common.djangoapps.track.segment')

from common.djangoapps.track.segment import *
