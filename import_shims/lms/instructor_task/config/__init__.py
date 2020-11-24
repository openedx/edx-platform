from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.config', 'lms.djangoapps.instructor_task.config')

from lms.djangoapps.instructor_task.config import *
