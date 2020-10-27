from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.users', 'lms.djangoapps.mobile_api.users')

from lms.djangoapps.mobile_api.users import *
