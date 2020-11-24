from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth', 'common.djangoapps.third_party_auth')

from common.djangoapps.third_party_auth import *
