from import_shims.warn import warn_deprecated_import

warn_deprecated_import('debug.management.commands', 'lms.djangoapps.debug.management.commands')

from lms.djangoapps.debug.management.commands import *
