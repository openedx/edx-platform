from import_shims.warn import warn_deprecated_import

warn_deprecated_import('mobile_api.course_info', 'lms.djangoapps.mobile_api.course_info')

from lms.djangoapps.mobile_api.course_info import *
