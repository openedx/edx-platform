from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'coursewarehistoryextended')

from lms.djangoapps.coursewarehistoryextended import *
