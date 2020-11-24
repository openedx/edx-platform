from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tasks_helper.grades', 'lms.djangoapps.instructor_task.tasks_helper.grades')

from lms.djangoapps.instructor_task.tasks_helper.grades import *
