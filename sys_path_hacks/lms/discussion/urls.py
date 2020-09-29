from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.urls')

from lms.djangoapps.discussion.urls import *
