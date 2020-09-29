from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.views')

from lms.djangoapps.discussion.views import *
