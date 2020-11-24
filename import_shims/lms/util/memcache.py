from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.memcache', 'common.djangoapps.util.memcache')

from common.djangoapps.util.memcache import *
