from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.tests.test_tasks', 'lms.djangoapps.certificates.tests.test_tasks')

from lms.djangoapps.certificates.tests.test_tasks import *
