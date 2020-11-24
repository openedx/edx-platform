from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.models', 'common.djangoapps.entitlements.models')

from common.djangoapps.entitlements.models import *
