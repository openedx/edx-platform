from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.admin', 'lms.djangoapps.instructor_task.admin')

from lms.djangoapps.instructor_task.admin import *
