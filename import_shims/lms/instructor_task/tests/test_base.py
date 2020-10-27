from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tests.test_base', 'lms.djangoapps.instructor_task.tests.test_base')

from lms.djangoapps.instructor_task.tests.test_base import *
