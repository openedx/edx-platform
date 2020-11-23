from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.api.views', 'lms.djangoapps.badges.api.views')

from lms.djangoapps.badges.api.views import *
