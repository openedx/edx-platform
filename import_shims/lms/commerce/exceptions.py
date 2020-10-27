from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.exceptions')

from lms.djangoapps.commerce.exceptions import *
