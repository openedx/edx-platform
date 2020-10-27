from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task')

from lms.djangoapps.instructor_task import *
