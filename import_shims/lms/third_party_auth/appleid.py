from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.appleid', 'common.djangoapps.third_party_auth.appleid')

from common.djangoapps.third_party_auth.appleid import *
