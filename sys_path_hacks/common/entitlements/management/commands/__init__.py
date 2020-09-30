from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.management.commands')

from common.djangoapps.entitlements.management.commands import *
