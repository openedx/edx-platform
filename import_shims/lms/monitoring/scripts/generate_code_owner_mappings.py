from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'monitoring.scripts.generate_code_owner_mappings')

from lms.djangoapps.monitoring.scripts.generate_code_owner_mappings import *
