from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'shoppingcart.processors.CyberSource2')

from lms.djangoapps.shoppingcart.processors.CyberSource2 import *
