from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.views.api')

from lms.djangoapps.instructor.views.api import *
