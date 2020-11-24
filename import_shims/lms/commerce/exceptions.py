from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.exceptions', 'lms.djangoapps.commerce.exceptions')

from lms.djangoapps.commerce.exceptions import *
