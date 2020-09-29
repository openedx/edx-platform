from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.views.tools')

from lms.djangoapps.instructor.views.tools import *
