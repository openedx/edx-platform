from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests.test_db', 'common.djangoapps.util.tests.test_db')

from common.djangoapps.util.tests.test_db import *
