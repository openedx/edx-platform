from import_shims.warn import warn_deprecated_import

warn_deprecated_import('third_party_auth.tasks', 'common.djangoapps.third_party_auth.tasks')

from common.djangoapps.third_party_auth.tasks import *
