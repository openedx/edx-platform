from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.models', 'common.djangoapps.util.models')

from common.djangoapps.util.models import *
