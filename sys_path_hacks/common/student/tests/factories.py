from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'student.tests.factories')

from common.djangoapps.student.tests.factories import *
