from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.tests.test_cert_management')

from lms.djangoapps.certificates.tests.test_cert_management import *
