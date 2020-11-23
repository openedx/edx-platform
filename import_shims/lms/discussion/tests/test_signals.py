from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.tests.test_signals', 'lms.djangoapps.discussion.tests.test_signals')

from lms.djangoapps.discussion.tests.test_signals import *
