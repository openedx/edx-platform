from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.tests')

from lms.djangoapps.dashboard.tests import *
