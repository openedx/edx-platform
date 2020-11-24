from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.exceptions', 'lms.djangoapps.instructor_task.exceptions')

from lms.djangoapps.instructor_task.exceptions import *
