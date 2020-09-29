from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.notifier_api.urls')

from lms.djangoapps.discussion.notifier_api.urls import *
