from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.urls')

from lms.djangoapps.shoppingcart.urls import *
