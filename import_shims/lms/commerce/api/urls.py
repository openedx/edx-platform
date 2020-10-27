from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.api.urls', 'lms.djangoapps.commerce.api.urls')

from lms.djangoapps.commerce.api.urls import *
