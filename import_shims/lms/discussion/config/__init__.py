from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.config', 'lms.djangoapps.discussion.config')

from lms.djangoapps.discussion.config import *
