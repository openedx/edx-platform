from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.utils')

from lms.djangoapps.commerce.utils import *
