from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.middleware', 'lms.djangoapps.mobile_api.middleware')

from lms.djangoapps.mobile_api.middleware import *
