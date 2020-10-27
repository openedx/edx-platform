from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.management.commands.tests.test_populate_expiry_date')

from lms.djangoapps.verify_student.management.commands.tests.test_populate_expiry_date import *
