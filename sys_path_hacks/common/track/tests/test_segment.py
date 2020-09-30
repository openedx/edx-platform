from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.tests.test_segment')

from common.djangoapps.track.tests.test_segment import *
