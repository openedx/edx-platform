from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.tests.test_payment_fake')

from lms.djangoapps.shoppingcart.tests.test_payment_fake import *
