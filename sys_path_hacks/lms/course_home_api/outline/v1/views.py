from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_home_api.outline.v1.views')

from lms.djangoapps.course_home_api.outline.v1.views import *
