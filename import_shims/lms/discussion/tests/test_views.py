from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.tests.test_views', 'lms.djangoapps.discussion.tests.test_views')

from lms.djangoapps.discussion.tests.test_views import *
