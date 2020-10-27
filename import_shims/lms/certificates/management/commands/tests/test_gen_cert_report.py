from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.management.commands.tests.test_gen_cert_report')

from lms.djangoapps.certificates.management.commands.tests.test_gen_cert_report import *
