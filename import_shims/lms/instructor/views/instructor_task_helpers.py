from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.views.instructor_task_helpers')

from lms.djangoapps.instructor.views.instructor_task_helpers import *
