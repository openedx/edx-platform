from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.backends.tests.test_logger')

from common.djangoapps.track.backends.tests.test_logger import *
