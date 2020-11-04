from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.tests.test_segment', 'common.djangoapps.track.tests.test_segment')

from common.djangoapps.track.tests.test_segment import *
