from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.rest_api.views', 'lms.djangoapps.discussion.rest_api.views')

from lms.djangoapps.discussion.rest_api.views import *
