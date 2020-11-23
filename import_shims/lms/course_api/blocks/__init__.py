from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.blocks', 'lms.djangoapps.course_api.blocks')

from lms.djangoapps.course_api.blocks import *
