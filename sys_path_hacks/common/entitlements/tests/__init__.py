from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.tests')

from common.djangoapps.entitlements.tests import *
