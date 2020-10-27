from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.backends', 'lms.djangoapps.badges.backends')

from lms.djangoapps.badges.backends import *
