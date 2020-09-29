from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.tasks')

from lms.djangoapps.grades.tasks import *
