from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.sysadmin')

from lms.djangoapps.dashboard.sysadmin import *
