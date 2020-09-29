from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.apps')

from lms.djangoapps.badges.apps import *
