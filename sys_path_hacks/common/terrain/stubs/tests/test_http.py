from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'terrain.stubs.tests.test_http')

from common.djangoapps.terrain.stubs.tests.test_http import *
