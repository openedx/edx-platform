from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.tests.integration.test_problems')

from lms.djangoapps.grades.tests.integration.test_problems import *
