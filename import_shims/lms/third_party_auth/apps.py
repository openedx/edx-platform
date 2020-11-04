from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.apps', 'common.djangoapps.third_party_auth.apps')

from common.djangoapps.third_party_auth.apps import *
