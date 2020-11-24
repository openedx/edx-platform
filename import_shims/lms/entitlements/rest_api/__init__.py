from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.rest_api', 'common.djangoapps.entitlements.rest_api')

from common.djangoapps.entitlements.rest_api import *
