from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.users.urls', 'lms.djangoapps.mobile_api.users.urls')

from lms.djangoapps.mobile_api.users.urls import *
