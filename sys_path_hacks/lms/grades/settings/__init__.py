from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.settings')

from lms.djangoapps.grades.settings import *
