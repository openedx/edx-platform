from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_home_api.mixins')

from lms.djangoapps.course_home_api.mixins import *
