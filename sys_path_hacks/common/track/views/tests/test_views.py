from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'track.views.tests.test_views')

from common.djangoapps.track.views.tests.test_views import *
