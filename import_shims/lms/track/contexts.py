from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.contexts', 'common.djangoapps.track.contexts')

from common.djangoapps.track.contexts import *
