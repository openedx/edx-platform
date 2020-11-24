from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.settings', 'lms.djangoapps.discussion.settings')

from lms.djangoapps.discussion.settings import *
