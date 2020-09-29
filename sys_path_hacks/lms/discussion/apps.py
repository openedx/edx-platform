from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.apps')

from lms.djangoapps.discussion.apps import *
