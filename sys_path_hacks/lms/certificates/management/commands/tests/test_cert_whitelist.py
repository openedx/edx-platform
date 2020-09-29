from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.management.commands.tests.test_cert_whitelist')

from lms.djangoapps.certificates.management.commands.tests.test_cert_whitelist import *
