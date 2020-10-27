from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.backends.tests.test_badgr_backend')

from lms.djangoapps.badges.backends.tests.test_badgr_backend import *
