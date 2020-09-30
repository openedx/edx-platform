from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.management.commands.tests.test_expire_old_entitlements')

from common.djangoapps.entitlements.management.commands.tests.test_expire_old_entitlements import *
