from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.management.commands.fail_old_tasks', 'lms.djangoapps.instructor_task.management.commands.fail_old_tasks')

from lms.djangoapps.instructor_task.management.commands.fail_old_tasks import *
