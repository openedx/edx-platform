from import_shims.warn import warn_deprecated_import

warn_deprecated_import('email_marketing.tests.test_signals', 'lms.djangoapps.email_marketing.tests.test_signals')

from lms.djangoapps.email_marketing.tests.test_signals import *
