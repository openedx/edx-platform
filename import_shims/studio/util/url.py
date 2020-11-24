from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.url', 'common.djangoapps.util.url')

from common.djangoapps.util.url import *
