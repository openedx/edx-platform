from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.tests.factories')

from common.djangoapps.entitlements.tests.factories import *
