from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.management.commands.saml', 'common.djangoapps.third_party_auth.management.commands.saml')

from common.djangoapps.third_party_auth.management.commands.saml import *
