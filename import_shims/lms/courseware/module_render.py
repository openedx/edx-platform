from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.module_render')

from lms.djangoapps.courseware.module_render import *
