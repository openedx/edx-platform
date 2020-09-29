from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'lms_xblock.field_data')

from lms.djangoapps.lms_xblock.field_data import *
