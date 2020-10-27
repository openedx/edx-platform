from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.handlers')

from lms.djangoapps.badges.handlers import *
