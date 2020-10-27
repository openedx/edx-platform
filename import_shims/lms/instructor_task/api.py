from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.api')

from lms.djangoapps.instructor_task.api import *
