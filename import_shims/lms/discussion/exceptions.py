from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.exceptions')

from lms.djangoapps.discussion.exceptions import *
