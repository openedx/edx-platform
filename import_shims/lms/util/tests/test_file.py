from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests.test_file', 'common.djangoapps.util.tests.test_file')

from common.djangoapps.util.tests.test_file import *
