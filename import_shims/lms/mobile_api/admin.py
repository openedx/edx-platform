from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.admin', 'lms.djangoapps.mobile_api.admin')

from lms.djangoapps.mobile_api.admin import *
