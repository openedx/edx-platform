from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard', 'lms.djangoapps.dashboard')

from lms.djangoapps.dashboard import *
