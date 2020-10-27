from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.management', 'lms.djangoapps.dashboard.management')

from lms.djangoapps.dashboard.management import *
