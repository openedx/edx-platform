from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.admin')

from common.djangoapps.entitlements.admin import *
