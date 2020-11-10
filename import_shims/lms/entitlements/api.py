from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.api', 'common.djangoapps.entitlements.api')

from common.djangoapps.entitlements.api import *
