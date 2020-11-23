from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.exceptions', 'common.djangoapps.third_party_auth.exceptions')

from common.djangoapps.third_party_auth.exceptions import *
