from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'bulk_email.tests.test_course_optout')

from lms.djangoapps.bulk_email.tests.test_course_optout import *
