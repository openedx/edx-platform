from import_shims.warn import warn_deprecated_import

warn_deprecated_import('status.models', 'common.djangoapps.status.models')

from common.djangoapps.status.models import *
