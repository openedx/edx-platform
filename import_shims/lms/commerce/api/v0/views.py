from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v0.views', 'lms.djangoapps.commerce.api.v0.views')

from lms.djangoapps.commerce.api.v0.views import *
