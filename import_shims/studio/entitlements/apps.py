from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.apps', 'common.djangoapps.entitlements.apps')

from common.djangoapps.entitlements.apps import *
