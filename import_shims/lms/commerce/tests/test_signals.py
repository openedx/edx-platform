from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.tests.test_signals')

from lms.djangoapps.commerce.tests.test_signals import *
