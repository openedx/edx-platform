from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.scores')

from lms.djangoapps.grades.scores import *
