from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.management')

from lms.djangoapps.commerce.management import *
