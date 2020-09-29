from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.signals.handlers')

from lms.djangoapps.discussion.signals.handlers import *
