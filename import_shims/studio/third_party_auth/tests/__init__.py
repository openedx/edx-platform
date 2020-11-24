from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.tests', 'common.djangoapps.third_party_auth.tests')

from common.djangoapps.third_party_auth.tests import *
