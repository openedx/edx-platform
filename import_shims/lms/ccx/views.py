from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.views')

from lms.djangoapps.ccx.views import *
