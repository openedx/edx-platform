from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.backends')

from lms.djangoapps.badges.backends import *
