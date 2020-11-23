from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.management.commands', 'common.djangoapps.third_party_auth.management.commands')

from common.djangoapps.third_party_auth.management.commands import *
