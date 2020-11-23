from import_shims.warn import warn_deprecated_import

warn_deprecated_import('bulk_email.tests.test_tasks', 'lms.djangoapps.bulk_email.tests.test_tasks')

from lms.djangoapps.bulk_email.tests.test_tasks import *
