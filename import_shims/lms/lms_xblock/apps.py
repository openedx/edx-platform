from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'lms_xblock.apps')

from lms.djangoapps.lms_xblock.apps import *
