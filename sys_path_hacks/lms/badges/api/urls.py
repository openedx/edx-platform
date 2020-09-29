from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.api.urls')

from lms.djangoapps.badges.api.urls import *
