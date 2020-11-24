from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.v1.urls', 'lms.djangoapps.commerce.api.v1.urls')

from lms.djangoapps.commerce.api.v1.urls import *
