from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.config.settings', 'lms.djangoapps.discussion.config.settings')

from lms.djangoapps.discussion.config.settings import *
