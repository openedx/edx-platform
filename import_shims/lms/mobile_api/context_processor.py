from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mobile_api.context_processor')

from lms.djangoapps.mobile_api.context_processor import *
