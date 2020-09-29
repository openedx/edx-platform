from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_blocks')

from lms.djangoapps.course_blocks import *
