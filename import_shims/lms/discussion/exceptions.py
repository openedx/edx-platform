from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.exceptions', 'lms.djangoapps.discussion.exceptions')

from lms.djangoapps.discussion.exceptions import *
