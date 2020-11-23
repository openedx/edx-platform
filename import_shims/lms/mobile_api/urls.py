from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.urls', 'lms.djangoapps.mobile_api.urls')

from lms.djangoapps.mobile_api.urls import *
