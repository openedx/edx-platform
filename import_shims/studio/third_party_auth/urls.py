from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.urls', 'common.djangoapps.third_party_auth.urls')

from common.djangoapps.third_party_auth.urls import *
