from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.signals')

from common.djangoapps.entitlements.signals import *
