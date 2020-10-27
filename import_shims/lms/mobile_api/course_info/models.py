from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mobile_api.course_info.models')

from lms.djangoapps.mobile_api.course_info.models import *
