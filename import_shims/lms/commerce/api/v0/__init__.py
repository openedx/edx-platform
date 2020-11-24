from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v0', 'lms.djangoapps.commerce.api.v0')

from lms.djangoapps.commerce.api.v0 import *
