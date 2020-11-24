from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.tests.test_admin', 'common.djangoapps.third_party_auth.tests.test_admin')

from common.djangoapps.third_party_auth.tests.test_admin import *
