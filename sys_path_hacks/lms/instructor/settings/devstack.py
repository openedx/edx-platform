from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'instructor.settings.devstack')

from lms.djangoapps.instructor.settings.devstack import *
