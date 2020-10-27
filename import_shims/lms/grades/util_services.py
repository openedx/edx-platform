from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'grades.util_services')

from lms.djangoapps.grades.util_services import *
