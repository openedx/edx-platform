from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.signals.handlers', 'lms.djangoapps.discussion.signals.handlers')

from lms.djangoapps.discussion.signals.handlers import *
