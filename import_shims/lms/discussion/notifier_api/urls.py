from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.notifier_api.urls', 'lms.djangoapps.discussion.notifier_api.urls')

from lms.djangoapps.discussion.notifier_api.urls import *
