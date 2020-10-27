from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.blocks.api', 'lms.djangoapps.course_api.blocks.api')

from lms.djangoapps.course_api.blocks.api import *
