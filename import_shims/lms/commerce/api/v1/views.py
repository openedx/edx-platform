from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v1.views', 'lms.djangoapps.commerce.api.v1.views')

from lms.djangoapps.commerce.api.v1.views import *
