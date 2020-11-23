from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.admin', 'lms.djangoapps.badges.admin')

from lms.djangoapps.badges.admin import *
