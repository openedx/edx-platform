from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.rest_api.urls', 'lms.djangoapps.discussion.rest_api.urls')

from lms.djangoapps.discussion.rest_api.urls import *
