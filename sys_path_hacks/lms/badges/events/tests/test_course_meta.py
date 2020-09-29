from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'badges.events.tests.test_course_meta')

from lms.djangoapps.badges.events.tests.test_course_meta import *
