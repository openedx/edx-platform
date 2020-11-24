from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.tests.test_provider', 'common.djangoapps.third_party_auth.tests.test_provider')

from common.djangoapps.third_party_auth.tests.test_provider import *
