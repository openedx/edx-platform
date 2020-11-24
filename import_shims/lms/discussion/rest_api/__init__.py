from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.rest_api', 'lms.djangoapps.discussion.rest_api')

from lms.djangoapps.discussion.rest_api import *
