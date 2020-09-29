from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_wiki.tests.test_access')

from lms.djangoapps.course_wiki.tests.test_access import *
