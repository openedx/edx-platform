from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.management.commands', 'lms.djangoapps.dashboard.management.commands')

from lms.djangoapps.dashboard.management.commands import *
