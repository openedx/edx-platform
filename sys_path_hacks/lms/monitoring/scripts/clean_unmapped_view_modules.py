from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'monitoring.scripts.clean_unmapped_view_modules')

from lms.djangoapps.monitoring.scripts.clean_unmapped_view_modules import *
