from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_blocks.transformers.user_partitions')

from lms.djangoapps.course_blocks.transformers.user_partitions import *
