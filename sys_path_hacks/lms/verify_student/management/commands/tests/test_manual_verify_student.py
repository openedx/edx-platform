from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.management.commands.tests.test_manual_verify_student')

from lms.djangoapps.verify_student.management.commands.tests.test_manual_verify_student import *
