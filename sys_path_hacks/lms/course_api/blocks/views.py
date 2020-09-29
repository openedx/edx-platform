from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_api.blocks.views')

from lms.djangoapps.course_api.blocks.views import *
