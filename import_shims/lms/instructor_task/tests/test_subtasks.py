from import_shims.warn import warn_deprecated_import

warn_deprecated_import('instructor_task.tests.test_subtasks', 'lms.djangoapps.instructor_task.tests.test_subtasks')

from lms.djangoapps.instructor_task.tests.test_subtasks import *
