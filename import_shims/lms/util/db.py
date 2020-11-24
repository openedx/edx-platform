from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.db', 'common.djangoapps.util.db')

from common.djangoapps.util.db import *
