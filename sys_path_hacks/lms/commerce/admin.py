from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.admin')

from lms.djangoapps.commerce.admin import *
