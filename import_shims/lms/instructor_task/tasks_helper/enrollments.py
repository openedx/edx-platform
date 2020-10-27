from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.tasks_helper.enrollments')

from lms.djangoapps.instructor_task.tasks_helper.enrollments import *
