from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_wiki.tests.test_comprehensive_theming')

from lms.djangoapps.course_wiki.tests.test_comprehensive_theming import *
