from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.git_import')

from lms.djangoapps.dashboard.git_import import *
