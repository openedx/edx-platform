from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.toggles')

from lms.djangoapps.courseware.toggles import *
