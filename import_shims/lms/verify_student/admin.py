from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.admin')

from lms.djangoapps.verify_student.admin import *
