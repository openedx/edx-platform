from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.modulestore')

from lms.djangoapps.ccx.modulestore import *
