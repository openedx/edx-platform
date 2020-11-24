from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.tests.test_tasks', 'lms.djangoapps.ccx.tests.test_tasks')

from lms.djangoapps.ccx.tests.test_tasks import *
