from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.tests.test_lti', 'common.djangoapps.third_party_auth.tests.test_lti')

from common.djangoapps.third_party_auth.tests.test_lti import *
