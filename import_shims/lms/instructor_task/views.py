from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.views')

from lms.djangoapps.instructor_task.views import *
