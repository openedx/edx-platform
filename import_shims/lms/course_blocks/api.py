from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_blocks.api', 'lms.djangoapps.course_blocks.api')

from lms.djangoapps.course_blocks.api import *
