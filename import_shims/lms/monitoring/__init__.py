from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'monitoring')

from lms.djangoapps.monitoring import *
