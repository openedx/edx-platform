from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.notification_prefs', 'lms.djangoapps.discussion.notification_prefs')

from lms.djangoapps.discussion.notification_prefs import *
