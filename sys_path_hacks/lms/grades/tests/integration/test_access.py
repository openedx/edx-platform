from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.tests.integration.test_access')

from lms.djangoapps.grades.tests.integration.test_access import *
