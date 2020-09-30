from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.management.commands.update_entitlement_mode')

from common.djangoapps.entitlements.management.commands.update_entitlement_mode import *
