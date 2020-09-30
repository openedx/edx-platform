from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'util.tests.test_disable_rate_limit')

from common.djangoapps.util.tests.test_disable_rate_limit import *
