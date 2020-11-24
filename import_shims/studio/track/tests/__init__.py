from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.tests', 'common.djangoapps.track.tests')

from common.djangoapps.track.tests import *
