from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.git_import', 'lms.djangoapps.dashboard.git_import')

from lms.djangoapps.dashboard.git_import import *
