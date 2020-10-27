from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.events', 'lms.djangoapps.badges.events')

from lms.djangoapps.badges.events import *
