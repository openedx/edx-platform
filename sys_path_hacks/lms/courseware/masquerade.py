from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.masquerade')

from lms.djangoapps.courseware.masquerade import *
