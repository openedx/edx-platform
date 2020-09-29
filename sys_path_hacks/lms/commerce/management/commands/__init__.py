from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.management.commands')

from lms.djangoapps.commerce.management.commands import *
