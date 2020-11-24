from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.backends.base', 'lms.djangoapps.badges.backends.base')

from lms.djangoapps.badges.backends.base import *
