from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.management.tests.test_retire_order')

from lms.djangoapps.shoppingcart.management.tests.test_retire_order import *
