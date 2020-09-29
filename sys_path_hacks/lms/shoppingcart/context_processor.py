from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.context_processor')

from lms.djangoapps.shoppingcart.context_processor import *
