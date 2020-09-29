from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.processors.tests')

from lms.djangoapps.shoppingcart.processors.tests import *
