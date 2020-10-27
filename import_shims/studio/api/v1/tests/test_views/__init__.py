from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'api.v1.tests.test_views')

from cms.djangoapps.api.v1.tests.test_views import *
