from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.access')

from lms.djangoapps.courseware.access import *
