from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.notification_prefs.views')

from lms.djangoapps.discussion.notification_prefs.views import *
