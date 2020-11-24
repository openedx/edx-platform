from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.rest_api.urls', 'common.djangoapps.entitlements.rest_api.urls')

from common.djangoapps.entitlements.rest_api.urls import *
