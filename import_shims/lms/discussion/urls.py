from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.urls', 'lms.djangoapps.discussion.urls')

from lms.djangoapps.discussion.urls import *
