from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'entitlements.tests.test_models')

from common.djangoapps.entitlements.tests.test_models import *
