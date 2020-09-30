from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.tests.test_tasks')

from common.djangoapps.student.tests.test_tasks import *
