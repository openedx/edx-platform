from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.apps', 'lms.djangoapps.mobile_api.apps')

from lms.djangoapps.mobile_api.apps import *
