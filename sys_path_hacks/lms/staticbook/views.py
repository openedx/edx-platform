from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'staticbook.views')

from lms.djangoapps.staticbook.views import *
