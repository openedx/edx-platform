from import_shims.warn import warn_deprecated_import

warn_deprecated_import('course_home_api.urls', 'lms.djangoapps.course_home_api.urls')

from lms.djangoapps.course_home_api.urls import *
