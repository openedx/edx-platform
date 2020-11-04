from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.saml', 'common.djangoapps.third_party_auth.saml')

from common.djangoapps.third_party_auth.saml import *
