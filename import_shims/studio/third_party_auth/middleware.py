from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.middleware', 'common.djangoapps.third_party_auth.middleware')

from common.djangoapps.third_party_auth.middleware import *
