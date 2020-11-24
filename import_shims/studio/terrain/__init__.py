from import_shims.warn import warn_deprecated_import

warn_deprecated_import('terrain', 'common.djangoapps.terrain')

from common.djangoapps.terrain import *
