from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.api.permissions', 'common.djangoapps.third_party_auth.api.permissions')

from common.djangoapps.third_party_auth.api.permissions import *
