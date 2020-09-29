from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.course_tools')

from lms.djangoapps.courseware.course_tools import *
