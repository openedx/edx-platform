from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.management')

from lms.djangoapps.dashboard.management import *
