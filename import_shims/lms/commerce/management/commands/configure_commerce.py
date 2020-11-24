from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.management.commands.configure_commerce', 'lms.djangoapps.commerce.management.commands.configure_commerce')

from lms.djangoapps.commerce.management.commands.configure_commerce import *
