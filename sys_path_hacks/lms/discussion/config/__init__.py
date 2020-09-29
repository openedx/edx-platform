from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.config')

from lms.djangoapps.discussion.config import *
