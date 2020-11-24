from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_blocks', 'lms.djangoapps.course_blocks')

from lms.djangoapps.course_blocks import *
