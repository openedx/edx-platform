from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_blocks.usage_info')

from lms.djangoapps.course_blocks.usage_info import *
