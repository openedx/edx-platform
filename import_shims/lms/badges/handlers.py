from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.handlers', 'lms.djangoapps.badges.handlers')

from lms.djangoapps.badges.handlers import *
