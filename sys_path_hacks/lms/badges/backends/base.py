from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.backends.base')

from lms.djangoapps.badges.backends.base import *
