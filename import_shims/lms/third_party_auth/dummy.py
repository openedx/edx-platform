from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.dummy', 'common.djangoapps.third_party_auth.dummy')

from common.djangoapps.third_party_auth.dummy import *
