from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce', 'lms.djangoapps.commerce')

from lms.djangoapps.commerce import *
