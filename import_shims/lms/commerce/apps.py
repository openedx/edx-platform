from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.apps')

from lms.djangoapps.commerce.apps import *
