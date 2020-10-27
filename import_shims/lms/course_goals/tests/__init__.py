from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_goals.tests')

from lms.djangoapps.course_goals.tests import *
