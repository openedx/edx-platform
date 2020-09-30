from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.views.tests.test_segmentio')

from common.djangoapps.track.views.tests.test_segmentio import *
