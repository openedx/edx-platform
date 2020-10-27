from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api', 'lms.djangoapps.mobile_api')

from lms.djangoapps.mobile_api import *
