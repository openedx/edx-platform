from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.http', 'lms.djangoapps.commerce.http')

from lms.djangoapps.commerce.http import *
