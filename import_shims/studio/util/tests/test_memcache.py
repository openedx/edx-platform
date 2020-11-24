from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests.test_memcache', 'common.djangoapps.util.tests.test_memcache')

from common.djangoapps.util.tests.test_memcache import *
