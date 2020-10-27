from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.tests.test_queue', 'lms.djangoapps.certificates.tests.test_queue')

from lms.djangoapps.certificates.tests.test_queue import *
