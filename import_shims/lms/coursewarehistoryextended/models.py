from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'coursewarehistoryextended.models')

from lms.djangoapps.coursewarehistoryextended.models import *
