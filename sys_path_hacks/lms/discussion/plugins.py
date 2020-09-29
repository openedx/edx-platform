from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.plugins')

from lms.djangoapps.discussion.plugins import *
