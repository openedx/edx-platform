from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.module_utils', 'common.djangoapps.util.module_utils')

from common.djangoapps.util.module_utils import *
