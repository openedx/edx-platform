from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.management', 'common.djangoapps.third_party_auth.management')

from common.djangoapps.third_party_auth.management import *
