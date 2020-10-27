from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.api', 'lms.djangoapps.badges.api')

from lms.djangoapps.badges.api import *
