from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.views.index')

from lms.djangoapps.support.views.index import *
