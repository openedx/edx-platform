from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.tests.test_views')

from lms.djangoapps.shoppingcart.tests.test_views import *
