from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tasks', 'lms.djangoapps.instructor_task.tasks')

from lms.djangoapps.instructor_task.tasks import *
