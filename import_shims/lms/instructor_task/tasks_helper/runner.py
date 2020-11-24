from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tasks_helper.runner', 'lms.djangoapps.instructor_task.tasks_helper.runner')

from lms.djangoapps.instructor_task.tasks_helper.runner import *
