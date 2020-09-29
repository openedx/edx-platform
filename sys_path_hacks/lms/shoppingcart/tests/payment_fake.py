from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.tests.payment_fake')

from lms.djangoapps.shoppingcart.tests.payment_fake import *
