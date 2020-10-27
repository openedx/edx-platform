from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tests.test_tasks', 'lms.djangoapps.lti_provider.tests.test_tasks')

from lms.djangoapps.lti_provider.tests.test_tasks import *
