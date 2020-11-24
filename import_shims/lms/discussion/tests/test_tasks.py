from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.tests.test_tasks', 'lms.djangoapps.discussion.tests.test_tasks')

from lms.djangoapps.discussion.tests.test_tasks import *
