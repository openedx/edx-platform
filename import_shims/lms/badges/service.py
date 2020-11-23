from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.service', 'lms.djangoapps.badges.service')

from lms.djangoapps.badges.service import *
