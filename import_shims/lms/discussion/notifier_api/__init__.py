from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.notifier_api', 'lms.djangoapps.discussion.notifier_api')

from lms.djangoapps.discussion.notifier_api import *
