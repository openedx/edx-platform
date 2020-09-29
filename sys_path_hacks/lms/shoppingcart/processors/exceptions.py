from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.processors.exceptions')

from lms.djangoapps.shoppingcart.processors.exceptions import *
