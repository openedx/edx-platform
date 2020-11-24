from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.settings', 'common.djangoapps.third_party_auth.settings')

from common.djangoapps.third_party_auth.settings import *
