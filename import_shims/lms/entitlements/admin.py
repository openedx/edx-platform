from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.admin', 'common.djangoapps.entitlements.admin')

from common.djangoapps.entitlements.admin import *
