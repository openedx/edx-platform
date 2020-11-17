from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.views', 'lms.djangoapps.discussion.views')

from lms.djangoapps.discussion.views import *
