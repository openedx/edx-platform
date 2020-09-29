from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'support.urls')

from lms.djangoapps.support.urls import *
