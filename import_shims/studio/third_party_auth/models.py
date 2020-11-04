from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.models', 'common.djangoapps.third_party_auth.models')

from common.djangoapps.third_party_auth.models import *
