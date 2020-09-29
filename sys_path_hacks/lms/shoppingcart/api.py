from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.api')

from lms.djangoapps.shoppingcart.api import *
