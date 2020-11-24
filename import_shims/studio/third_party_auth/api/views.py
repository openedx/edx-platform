from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.api.views', 'common.djangoapps.third_party_auth.api.views')

from common.djangoapps.third_party_auth.api.views import *
