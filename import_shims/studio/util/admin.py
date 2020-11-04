from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.admin', 'common.djangoapps.util.admin')

from common.djangoapps.util.admin import *
