from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.tests.test_api', 'lms.djangoapps.certificates.tests.test_api')

from lms.djangoapps.certificates.tests.test_api import *
