from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.overrides')

from lms.djangoapps.ccx.overrides import *
