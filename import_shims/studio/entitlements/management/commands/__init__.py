from import_shims.warn import warn_deprecated_import

warn_deprecated_import('entitlements.management.commands', 'common.djangoapps.entitlements.management.commands')

from common.djangoapps.entitlements.management.commands import *
