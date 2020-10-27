from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'dashboard.sysadmin_urls')

from lms.djangoapps.dashboard.sysadmin_urls import *
