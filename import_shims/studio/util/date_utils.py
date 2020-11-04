from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.date_utils', 'common.djangoapps.util.date_utils')

from common.djangoapps.util.date_utils import *
