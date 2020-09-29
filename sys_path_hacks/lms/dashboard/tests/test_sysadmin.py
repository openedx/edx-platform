from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.tests.test_sysadmin')

from lms.djangoapps.dashboard.tests.test_sysadmin import *
