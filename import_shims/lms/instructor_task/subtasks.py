from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.subtasks', 'lms.djangoapps.instructor_task.subtasks')

from lms.djangoapps.instructor_task.subtasks import *
