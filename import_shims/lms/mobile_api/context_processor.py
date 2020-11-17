from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.context_processor', 'lms.djangoapps.mobile_api.context_processor')

from lms.djangoapps.mobile_api.context_processor import *
