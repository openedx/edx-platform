from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.admin')

from lms.djangoapps.shoppingcart.admin import *
