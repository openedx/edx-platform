from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.admin', 'common.djangoapps.third_party_auth.admin')

from common.djangoapps.third_party_auth.admin import *
