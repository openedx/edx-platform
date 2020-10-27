from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'lms_xblock.admin')

from lms.djangoapps.lms_xblock.admin import *
