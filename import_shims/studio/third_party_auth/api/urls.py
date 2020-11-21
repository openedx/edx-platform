from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.api.urls', 'common.djangoapps.third_party_auth.api.urls')

from common.djangoapps.third_party_auth.api.urls import *
