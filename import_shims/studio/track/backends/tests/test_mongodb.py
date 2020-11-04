from import_shims.warn import warn_deprecated_import

warn_deprecated_import('track.backends.tests.test_mongodb', 'common.djangoapps.track.backends.tests.test_mongodb')

from common.djangoapps.track.backends.tests.test_mongodb import *
