from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.api', 'lms.djangoapps.instructor_task.api')

from lms.djangoapps.instructor_task.api import *
