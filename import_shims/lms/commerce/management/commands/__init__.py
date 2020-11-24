from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.management.commands', 'lms.djangoapps.commerce.management.commands')

from lms.djangoapps.commerce.management.commands import *
