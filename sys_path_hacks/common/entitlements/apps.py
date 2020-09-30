from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.apps')

from common.djangoapps.entitlements.apps import *
