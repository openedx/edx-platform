from import_shims.warn import warn_deprecated_import

warn_deprecated_import('commerce.tests.test_signals', 'lms.djangoapps.commerce.tests.test_signals')

from lms.djangoapps.commerce.tests.test_signals import *
