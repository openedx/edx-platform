from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'debug.management')

from lms.djangoapps.debug.management import *
