from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tests', 'lms.djangoapps.instructor_task.tests')

from lms.djangoapps.instructor_task.tests import *
