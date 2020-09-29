from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.views')

from lms.djangoapps.shoppingcart.views import *
