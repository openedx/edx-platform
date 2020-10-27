from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.settings.common')

from lms.djangoapps.discussion.settings.common import *
