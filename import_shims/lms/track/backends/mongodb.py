from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.backends.mongodb', 'common.djangoapps.track.backends.mongodb')

from common.djangoapps.track.backends.mongodb import *
