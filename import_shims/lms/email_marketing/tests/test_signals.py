from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'email_marketing.tests.test_signals')

from lms.djangoapps.email_marketing.tests.test_signals import *
