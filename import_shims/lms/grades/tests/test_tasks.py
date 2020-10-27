from import_shims.warn import warn_deprecated_import

warn_deprecated_import('grades.tests.test_tasks', 'lms.djangoapps.grades.tests.test_tasks')

from lms.djangoapps.grades.tests.test_tasks import *
