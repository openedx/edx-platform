from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.views', 'common.djangoapps.third_party_auth.views')

from common.djangoapps.third_party_auth.views import *
