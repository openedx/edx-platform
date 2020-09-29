from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor_task.config.models')

from lms.djangoapps.instructor_task.config.models import *
