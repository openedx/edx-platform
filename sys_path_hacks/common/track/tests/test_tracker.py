from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.tests.test_tracker')

from common.djangoapps.track.tests.test_tracker import *
