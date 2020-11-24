from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v1', 'lms.djangoapps.commerce.api.v1')

from lms.djangoapps.commerce.api.v1 import *
