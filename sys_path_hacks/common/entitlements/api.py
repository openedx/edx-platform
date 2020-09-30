from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.api')

from common.djangoapps.entitlements.api import *
