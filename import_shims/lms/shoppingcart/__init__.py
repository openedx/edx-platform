from import_shims.warn import warn_deprecated_import

warn_deprecated_import('shoppingcart', 'lms.djangoapps.shoppingcart')

from lms.djangoapps.shoppingcart import *
