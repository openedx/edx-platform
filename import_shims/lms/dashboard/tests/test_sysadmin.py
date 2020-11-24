from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.tests.test_sysadmin', 'lms.djangoapps.dashboard.tests.test_sysadmin')

from lms.djangoapps.dashboard.tests.test_sysadmin import *
