from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.models', 'lms.djangoapps.dashboard.models')

from lms.djangoapps.dashboard.models import *
