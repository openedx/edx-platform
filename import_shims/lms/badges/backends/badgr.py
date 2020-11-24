from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.backends.badgr', 'lms.djangoapps.badges.backends.badgr')

from lms.djangoapps.badges.backends.badgr import *
