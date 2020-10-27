from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.course_info.urls', 'lms.djangoapps.mobile_api.course_info.urls')

from lms.djangoapps.mobile_api.course_info.urls import *
