from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.rest_api.tests', 'lms.djangoapps.discussion.rest_api.tests')

from lms.djangoapps.discussion.rest_api.tests import *
