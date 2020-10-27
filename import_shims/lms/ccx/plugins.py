from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.plugins')

from lms.djangoapps.ccx.plugins import *
