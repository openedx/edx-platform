from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.tests.test_fake_software_secure')

from lms.djangoapps.verify_student.tests.test_fake_software_secure import *
