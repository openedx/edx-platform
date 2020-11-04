from import_shims.warn import warn_deprecated_import

warn_deprecated_import('database_fixups', 'common.djangoapps.database_fixups')

from common.djangoapps.database_fixups import *
