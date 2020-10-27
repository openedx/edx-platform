from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'debug.views')

from lms.djangoapps.debug.views import *
