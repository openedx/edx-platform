from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.query', 'common.djangoapps.util.query')

from common.djangoapps.util.query import *
