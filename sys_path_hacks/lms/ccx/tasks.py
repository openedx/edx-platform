from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'ccx.tasks')

from lms.djangoapps.ccx.tasks import *
