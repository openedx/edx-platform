from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.settings.test')

from lms.djangoapps.instructor.settings.test import *
