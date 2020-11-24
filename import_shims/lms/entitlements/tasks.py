from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.tasks', 'common.djangoapps.entitlements.tasks')

from common.djangoapps.entitlements.tasks import *
