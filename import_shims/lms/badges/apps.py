from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.apps', 'lms.djangoapps.badges.apps')

from lms.djangoapps.badges.apps import *
