from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tests.test_credit_requirements')

from lms.djangoapps.courseware.tests.test_credit_requirements import *
