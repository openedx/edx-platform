from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.tests.test_services', 'lms.djangoapps.certificates.tests.test_services')

from lms.djangoapps.certificates.tests.test_services import *
