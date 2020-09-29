from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.context_processor')

from lms.djangoapps.courseware.context_processor import *
