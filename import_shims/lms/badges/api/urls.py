from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.api.urls', 'lms.djangoapps.badges.api.urls')

from lms.djangoapps.badges.api.urls import *
