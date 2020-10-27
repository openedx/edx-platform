from import_shims.warn import warn_deprecated_import

warn_deprecated_import('tests.test_utils', 'lms.djangoapps.tests.test_utils')

from lms.djangoapps.tests.test_utils import *
