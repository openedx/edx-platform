from import_shims.warn import warn_deprecated_import

warn_deprecated_import('debug', 'lms.djangoapps.debug')

from lms.djangoapps.debug import *
