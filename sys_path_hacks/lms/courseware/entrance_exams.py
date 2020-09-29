from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.entrance_exams')

from lms.djangoapps.courseware.entrance_exams import *
