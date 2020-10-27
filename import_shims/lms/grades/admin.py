from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.admin')

from lms.djangoapps.grades.admin import *
