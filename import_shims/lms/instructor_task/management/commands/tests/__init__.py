from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.management.commands.tests')

from lms.djangoapps.instructor_task.management.commands.tests import *
