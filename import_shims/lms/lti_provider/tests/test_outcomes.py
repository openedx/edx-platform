from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tests.test_outcomes', 'lms.djangoapps.lti_provider.tests.test_outcomes')

from lms.djangoapps.lti_provider.tests.test_outcomes import *
