from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v0.urls', 'lms.djangoapps.commerce.api.v0.urls')

from lms.djangoapps.commerce.api.v0.urls import *
