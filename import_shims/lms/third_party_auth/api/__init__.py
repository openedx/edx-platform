from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.api', 'common.djangoapps.third_party_auth.api')

from common.djangoapps.third_party_auth.api import *
