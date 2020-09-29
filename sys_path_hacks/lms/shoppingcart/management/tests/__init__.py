from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.management.tests')

from lms.djangoapps.shoppingcart.management.tests import *
