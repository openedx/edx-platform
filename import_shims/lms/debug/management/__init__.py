from import_shims.warn import warn_deprecated_import

warn_deprecated_import('debug.management', 'lms.djangoapps.debug.management')

from lms.djangoapps.debug.management import *
