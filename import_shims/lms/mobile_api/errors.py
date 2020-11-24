from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.errors', 'lms.djangoapps.mobile_api.errors')

from lms.djangoapps.mobile_api.errors import *
