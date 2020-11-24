from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.models', 'lms.djangoapps.badges.models')

from lms.djangoapps.badges.models import *
