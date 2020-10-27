from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.models', 'lms.djangoapps.mobile_api.models')

from lms.djangoapps.mobile_api.models import *
