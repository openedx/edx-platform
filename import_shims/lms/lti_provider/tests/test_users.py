from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tests.test_users', 'lms.djangoapps.lti_provider.tests.test_users')

from lms.djangoapps.lti_provider.tests.test_users import *
