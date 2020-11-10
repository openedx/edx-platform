from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.tests.test_tracker', 'common.djangoapps.track.tests.test_tracker')

from common.djangoapps.track.tests.test_tracker import *
