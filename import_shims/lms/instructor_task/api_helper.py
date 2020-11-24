from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.api_helper', 'lms.djangoapps.instructor_task.api_helper')

from lms.djangoapps.instructor_task.api_helper import *
