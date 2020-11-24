from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.provider', 'common.djangoapps.third_party_auth.provider')

from common.djangoapps.third_party_auth.provider import *
