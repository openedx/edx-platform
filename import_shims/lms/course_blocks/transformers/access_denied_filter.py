from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_blocks.transformers.access_denied_filter')

from lms.djangoapps.course_blocks.transformers.access_denied_filter import *
