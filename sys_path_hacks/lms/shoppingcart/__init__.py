from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart')

from lms.djangoapps.shoppingcart import *
