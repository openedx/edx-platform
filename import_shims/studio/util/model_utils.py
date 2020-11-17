from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.model_utils', 'common.djangoapps.util.model_utils')

from common.djangoapps.util.model_utils import *
