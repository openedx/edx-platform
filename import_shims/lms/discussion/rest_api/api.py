from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.rest_api.api', 'lms.djangoapps.discussion.rest_api.api')

from lms.djangoapps.discussion.rest_api.api import *
