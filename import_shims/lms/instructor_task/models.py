from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.models', 'lms.djangoapps.instructor_task.models')

from lms.djangoapps.instructor_task.models import *
