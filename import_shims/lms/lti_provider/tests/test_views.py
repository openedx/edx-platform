from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tests.test_views', 'lms.djangoapps.lti_provider.tests.test_views')

from lms.djangoapps.lti_provider.tests.test_views import *
