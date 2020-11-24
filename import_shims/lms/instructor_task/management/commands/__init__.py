from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.management.commands', 'lms.djangoapps.instructor_task.management.commands')

from lms.djangoapps.instructor_task.management.commands import *
