from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_api.blocks.urls', 'lms.djangoapps.course_api.blocks.urls')

from lms.djangoapps.course_api.blocks.urls import *
