from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task', 'lms.djangoapps.instructor_task')

from lms.djangoapps.instructor_task import *
