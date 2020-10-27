from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.custom_exception')

from lms.djangoapps.ccx.custom_exception import *
