from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.utils')

from common.djangoapps.entitlements.utils import *
