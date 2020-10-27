from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.tabs')

from lms.djangoapps.courseware.tabs import *
