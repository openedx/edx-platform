from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.exceptions')

from lms.djangoapps.courseware.exceptions import *
