from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.management.commands.fail_old_tasks')

from lms.djangoapps.instructor_task.management.commands.fail_old_tasks import *
