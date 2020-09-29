from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.notification_prefs.tests')

from lms.djangoapps.discussion.notification_prefs.tests import *
