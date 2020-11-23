from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.management', 'lms.djangoapps.instructor_task.management')

from lms.djangoapps.instructor_task.management import *
