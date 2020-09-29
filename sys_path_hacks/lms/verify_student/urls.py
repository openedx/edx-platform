from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'verify_student.urls')

from lms.djangoapps.verify_student.urls import *
